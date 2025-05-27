#!/usr/bin/env python

"""
Script to list all AWS resource ARNs in an AWS account across all available regions.
Credentials are sourced from environment variables.
"""

from datetime import datetime
import concurrent.futures
import sys
import json
import botocore
import boto3


def get_session():
    """Create a boto3 session using environment variables for credentials."""
    return boto3.Session()


def get_all_regions():
    """Get a list of all available AWS regions."""
    try:
        session = get_session()
        ec2_client = session.client('ec2', region_name='us-east-1')
        regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
        return regions
    except Exception as e:
        print(f"Error getting AWS regions: {e}")
        print("Falling back to a default list of major AWS regions")
        return [
            'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
            'ca-central-1', 'eu-west-1', 'eu-west-2', 'eu-west-3',
            'eu-central-1', 'eu-north-1', 'ap-northeast-1',
            'ap-northeast-2', 'ap-southeast-1', 'ap-southeast-2',
            'ap-south-1', 'sa-east-1'
        ]


def extract_resource_identifier_from_arn(arn_string):
    """
    Extracts the resource identifier part from an AWS ARN.
    Example: arn:partition:service:region:account-id:resource -> resource
             arn:partition:service:region:account-id:resourcetype/resourceid -> resourcetype/resourceid
    """
    if not isinstance(arn_string, str) or not arn_string.startswith("arn:"):
        return "Unknown_Invalid_ARN_Format"
    try:
        parts = arn_string.split(':', 5)
        if len(parts) > 5:
            return parts[5]

        # Handles cases like S3 bucket ARNs (arn:aws:s3:::bucket-name)
        # or ARNs that don't have a resource type/id qualifier after the 5th colon.
        if len(parts) == 5 and parts[4] == '' and parts[3] != '':  # e.g. arn:aws:s3:::bucket (parts[5] doesn't exist)
            # This is likely an S3 bucket ARN format, where the bucket name is the resource.
            # However, our split by 5 colons might not give us the bucket name directly if there are no further colons.
            # The standard split by 6 parts (':' , 5) should handle it.
            # If parts[5] is empty, it implies the resource part is empty or not present in typical form.
            # For S3: arn:aws:s3:::mybucket -> parts = ['arn', 'aws', 's3', '', '', 'mybucket']
            # Let's adjust for S3 like ARNs specifically if needed, but the current split should be okay.
            # If ARN is "arn:aws:s3:::my-bucket", split(':',5) gives ['arn', 'aws', 's3', '', '', 'my-bucket']
            # If ARN is "arn:aws:iam::123456789012:root" split(':',5) gives ['arn', 'aws', 'iam', '', '123456789012', 'root']
            # This part might need more refinement if we encounter ARNs that don't fit the typical patterns.
            # For now, if parts[5] is missing, it's an issue.
            return "Unknown_Short_Or_Malformed_ARN"

        # If the ARN is for a service itself, not a specific resource, parts[5] might be absent or different.
        # e.g. arn:aws:iam::123456789012:root - parts[5] is 'root'
        # e.g. arn:aws:s3:::bucket_name - parts[5] is 'bucket_name'
        # The original logic: if len(parts) > 5: return parts[5] should cover most cases.
        # If not, it means the resource identifier is not in the 6th segment.
        # This could be an account-level ARN or a malformed one.
        return "Identifier_Not_In_Expected_Segment"

    except Exception:  # Catch any parsing error
        return "Unknown_Error_Parsing_ARN"


def collect_resource_arns(service_name, region, arns_dict):
    """Collect ARNs for a specific service in the specified region."""
    try:
        session = get_session()
        client = session.client(service_name, region_name=region)
        account_id = session.client('sts').get_caller_identity()['Account']  # Get account_id once

        def extract_service_from_arn(arn):
            """Extracts the service name from an ARN."""
            parts = arn.split(':')
            if len(parts) >= 3:
                return parts[2]
            return 'Unknown_Service_In_ARN'

        # Collection strategies by service
        if service_name == 'elbv2':
            try:
                paginator = client.get_paginator('describe_load_balancers')
                for page in paginator.paginate():
                    for lb in page.get('LoadBalancers', []):
                        lb_type = lb.get('Type', 'unknown').lower()
                        endpoint = lb.get('DNSName', 'Unknown')
                        arn = lb['LoadBalancerArn']
                        service = extract_service_from_arn(arn)
                        resource_id_name = extract_resource_identifier_from_arn(arn)
                        common_data = {
                            'arn': arn,
                            'name': resource_id_name,
                            'subclass': service,
                            'region': region,
                            'endpoint': endpoint,
                            'scheme': lb.get('Scheme', 'Unknown'),
                            'creation_date': lb.get('CreatedTime', 'Unknown').isoformat() if hasattr(lb.get('CreatedTime', 'Unknown'), 'isoformat') else str(lb.get('CreatedTime', 'Unknown'))
                        }
                        if lb_type == 'application':
                            arns_dict.setdefault('alb', []).append(common_data)
                        elif lb_type == 'network':
                            arns_dict.setdefault('nlb', []).append(common_data)
            except Exception as e:
                if "OptInRequired" not in str(e):
                    print(f"Error listing ELBv2 load balancers in {region}: {e}")

        elif service_name == 'elb':
            try:
                paginator = client.get_paginator('describe_load_balancers')
                for page in paginator.paginate():
                    for lb in page.get('LoadBalancerDescriptions', []):
                        lb_name_val = lb['LoadBalancerName']
                        endpoint = lb.get('DNSName', 'Unknown')
                        arn = f"arn:aws:elasticloadbalancing:{region}:{account_id}:loadbalancer/{lb_name_val}"
                        service = extract_service_from_arn(arn)
                        resource_id_name = extract_resource_identifier_from_arn(arn)
                        arns_dict.setdefault('classic_elb', []).append({
                            'arn': arn,
                            'name': resource_id_name,
                            'subclass': service,
                            'region': region,
                            'endpoint': endpoint,
                            'scheme': lb.get('Scheme', 'Unknown'),
                            'creation_date': lb.get('CreatedTime', 'Unknown').isoformat() if hasattr(lb.get('CreatedTime', 'Unknown'), 'isoformat') else str(lb.get('CreatedTime', 'Unknown'))
                        })
            except Exception as e:
                if "OptInRequired" not in str(e):
                    print(f"Error listing Classic ELB load balancers in {region}: {e}")

        elif service_name == 's3':
            if region == 'us-east-1':  # S3 list_buckets is global
                try:
                    response = client.list_buckets()  # No paginator for list_buckets
                    for bucket in response.get('Buckets', []):
                        bucket_name_val = bucket['Name']
                        bucket_region = region  # Default to current region, then try to get specific
                        endpoint = f"https://{bucket_name_val}.s3.amazonaws.com"  # Default endpoint
                        try:
                            bucket_location = client.get_bucket_location(Bucket=bucket_name_val)
                            loc_constraint = bucket_location.get('LocationConstraint')
                            if loc_constraint:  # Can be None for us-east-1
                                bucket_region = loc_constraint
                            # For us-east-1, LocationConstraint is None or 'us-east-1'.
                            # Other regions return their name, e.g., 'eu-west-1'.
                            if bucket_region == 'US':
                                bucket_region = 'us-east-1'  # Some legacy buckets might return 'US'

                            if bucket_region and bucket_region != 'us-east-1':
                                endpoint = f"https://{bucket_name_val}.s3.{bucket_region}.amazonaws.com"
                            else:  # us-east-1 or None
                                bucket_region = 'us-east-1'  # Standardize
                                endpoint = f"https://{bucket_name_val}.s3.{bucket_region}.amazonaws.com"

                        except Exception as loc_e:
                            print(f"Warning: Could not get location for bucket {bucket_name_val}, defaulting to us-east-1 endpoint. Error: {loc_e}")
                            bucket_region = 'us-east-1'  # Fallback

                        arn = f"arn:aws:s3:::{bucket_name_val}"
                        service = extract_service_from_arn(arn)
                        resource_id_name = extract_resource_identifier_from_arn(arn)
                        arns_dict.setdefault(service_name, []).append({
                            'arn': arn,
                            'name': resource_id_name,
                            'subclass': service,
                            'region': bucket_region,  # Store actual bucket region
                            'endpoint': endpoint,
                            'account': account_id,
                            'creation_date': bucket.get('CreationDate', 'Unknown').isoformat() if hasattr(bucket.get('CreationDate', 'Unknown'), 'isoformat') else str(bucket.get('CreationDate', 'Unknown'))
                        })
                except Exception as e:
                    print(f"Error listing S3 buckets: {e}")

        elif service_name == 'ec2':
            try:  # EC2 Instances
                paginator = client.get_paginator('describe_instances')
                for page in paginator.paginate():
                    for reservation in page.get('Reservations', []):
                        for instance in reservation.get('Instances', []):
                            instance_id = instance['InstanceId']
                            arn = f"arn:aws:ec2:{region}:{account_id}:instance/{instance_id}"
                            service = extract_service_from_arn(arn)
                            resource_id_name = extract_resource_identifier_from_arn(arn)
                            arns_dict.setdefault(service_name, []).append({  # service_name is 'ec2'
                                'arn': arn,
                                'name': resource_id_name,
                                'subclass': service,
                                'region': region,
                                'private_ip': instance.get('PrivateIpAddress', 'None'),
                                'public_ip': instance.get('PublicIpAddress', 'None'),
                                'creation_date': instance.get('LaunchTime', 'Unknown').isoformat() if hasattr(instance.get('LaunchTime', 'Unknown'), 'isoformat') else str(instance.get('LaunchTime', 'Unknown'))
                            })
            except Exception as e:
                if "OptInRequired" not in str(e):
                    print(f"Error listing EC2 instances in {region}: {e}")

            # try:  # VPCs
            #     paginator = client.get_paginator('describe_vpcs')
            #     for page in paginator.paginate():
            #         for vpc in page.get('Vpcs', []):
            #             vpc_id = vpc['VpcId']
            #             arn = f"arn:aws:ec2:{region}:{account_id}:vpc/{vpc_id}"
            #             service = extract_service_from_arn(arn)
            #             resource_id_name = extract_resource_identifier_from_arn(arn)
            #             arns_dict.setdefault('vpc', []).append({
            #                 'arn': arn,
            #                 'name': resource_id_name,
            #                 'subclass': service,
            #                 'region': region,
            #                 'cidr': vpc.get('CidrBlock', 'Unknown'),
            #                 'creation_date': 'Unknown'  # VPCs don't have a direct creation date via this API
            #             })
            # except Exception as e:
            #     if "OptInRequired" not in str(e):
            #         print(f"Error listing VPCs in {region}: {e}")

        elif service_name == 'lambda':
            try:
                paginator = client.get_paginator('list_functions')
                for page in paginator.paginate():
                    for function in page.get('Functions', []):
                        arn = function['FunctionArn']
                        service = extract_service_from_arn(arn)
                        resource_id_name = extract_resource_identifier_from_arn(arn)
                        arns_dict.setdefault(service_name, []).append({
                            'arn': arn,
                            'name': resource_id_name,
                            'subclass': service,
                            'region': region,
                            'creation_date': function.get('LastModified', 'Unknown')  # LastModified is a string
                        })
            except Exception as e:
                if "OptInRequired" not in str(e):
                    print(f"Error listing Lambda functions in {region}: {e}")

        elif service_name == 'rds':
            try:
                paginator = client.get_paginator('describe_db_instances')
                for page in paginator.paginate():
                    for instance in page.get('DBInstances', []):
                        arn = instance['DBInstanceArn']
                        service = extract_service_from_arn(arn)
                        resource_id_name = extract_resource_identifier_from_arn(arn)
                        arns_dict.setdefault(service_name, []).append({
                            'arn': arn,
                            'name': resource_id_name,
                            'subclass': service,
                            'region': region,
                            'creation_date': instance.get('InstanceCreateTime', 'Unknown').isoformat() if hasattr(instance.get('InstanceCreateTime', 'Unknown'), 'isoformat') else str(instance.get('InstanceCreateTime', 'Unknown'))
                        })
            except Exception as e:
                if "OptInRequired" not in str(e):
                    print(f"Error listing RDS instances in {region}: {e}")

        elif service_name == 'dynamodb':
            try:
                paginator = client.get_paginator('list_tables')
                for page in paginator.paginate():
                    for table_name_val in page.get('TableNames', []):
                        arn = f"arn:aws:dynamodb:{region}:{account_id}:table/{table_name_val}"
                        creation_date = 'Unknown'
                        try:
                            table_details = client.describe_table(TableName=table_name_val)
                            creation_date_dt = table_details.get('Table', {}).get('CreationDateTime', 'Unknown')
                            creation_date = creation_date_dt.isoformat() if hasattr(creation_date_dt, 'isoformat') else str(creation_date_dt)
                        except Exception as desc_e:
                            print(f"Warning: Could not describe DynamoDB table {table_name_val} for creation date: {desc_e}")
                        service = extract_service_from_arn(arn)
                        resource_id_name = extract_resource_identifier_from_arn(arn)
                        arns_dict.setdefault(service_name, []).append({
                            'arn': arn,
                            'name': resource_id_name,
                            'subclass': service,
                            'region': region,
                            'creation_date': creation_date
                        })
            except Exception as e:
                if "OptInRequired" not in str(e):
                    print(f"Error listing DynamoDB tables in {region}: {e}")

        elif service_name == 'sns':
            try:
                paginator = client.get_paginator('list_topics')
                for page in paginator.paginate():
                    for topic in page.get('Topics', []):
                        arn = topic['TopicArn']
                        service = extract_service_from_arn(arn)
                        resource_id_name = extract_resource_identifier_from_arn(arn)
                        arns_dict.setdefault(service_name, []).append({
                            'arn': arn,
                            'name': resource_id_name,
                            'subclass': service,
                            'region': region,
                            'creation_date': 'Unknown'  # SNS Topics don't have a direct creation date via this API
                        })
            except Exception as e:
                if "OptInRequired" not in str(e):
                    print(f"Error listing SNS topics in {region}: {e}")

        elif service_name == 'sqs':
            try:
                paginator = client.get_paginator('list_queues')
                for page in paginator.paginate():
                    for queue_url in page.get('QueueUrls', []):
                        try:
                            queue_attrs = client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['QueueArn', 'CreatedTimestamp'])
                            arn = queue_attrs.get('Attributes', {}).get('QueueArn')
                            if not arn:
                                continue  # Skip if ARN not found
                            
                            created_timestamp_str = queue_attrs.get('Attributes', {}).get('CreatedTimestamp', 'Unknown')
                            creation_date = 'Unknown'
                            if created_timestamp_str.isdigit():
                                creation_date = datetime.fromtimestamp(int(created_timestamp_str)).isoformat()
                            
                            service = extract_service_from_arn(arn)
                            resource_id_name = extract_resource_identifier_from_arn(arn)
                            arns_dict.setdefault(service_name, []).append({
                                'arn': arn,
                                'name': resource_id_name,
                                'subclass': service,
                                'region': region,
                                'creation_date': creation_date
                            })
                        except Exception as attr_e:
                            print(f"Error getting attributes for SQS queue {queue_url}: {attr_e}")
            except Exception as e:
                if "OptInRequired" not in str(e):
                    print(f"Error listing SQS queues in {region}: {e}")

        elif service_name == 'iam':
            if region == 'us-east-1':  # IAM is global, process only once
                iam_item_configs = [
                    # item_type, operation_name, items_key, date_key, paginate_params
                    ('role', 'list_roles', 'Roles', 'CreateDate', {}),
                    ('user', 'list_users', 'Users', 'CreateDate', {}),
                    ('policy', 'list_policies', 'Policies', 'CreateDate', {'Scope': 'Local'})  # Customer managed policies
                ]

                for item_type, op_name, items_key_str, date_key_str, params_paginate in iam_item_configs:
                    try:
                        paginator = client.get_paginator(op_name)
                        for page in paginator.paginate(**params_paginate):
                            for item in page.get(items_key_str, []):
                                arn = item.get('Arn')
                                if not isinstance(arn, str):
                                    print(f"Warning: IAM {item_type} item found with invalid ARN '{arn}'. Item data: {item}")
                                    continue

                                service = extract_service_from_arn(arn)
                                resource_id_name = extract_resource_identifier_from_arn(arn)
                                creation_date_val = item.get(date_key_str, 'Unknown')
                                creation_date_iso = creation_date_val.isoformat() if hasattr(creation_date_val, 'isoformat') else str(creation_date_val)

                                arns_dict.setdefault(service_name, []).append({
                                    'arn': arn,
                                    'name': resource_id_name,
                                    'subclass': service,
                                    'item_type': item_type,
                                    'region': 'global',
                                    'creation_date': creation_date_iso
                                })
                    except botocore.exceptions.ClientError as ce:
                        print(f"AWS ClientError listing IAM {item_type}s in {region}: {ce}. This could be a permissions issue or the service is not available in the region for this account.")
                    except Exception as item_e:
                        print(f"Unexpected error listing IAM {item_type}s in {region}: {item_e}")
            # No else needed, IAM is global and processed in us-east-1 only.

        elif service_name == 'cloudformation':
            try:
                paginator = client.get_paginator('list_stacks')
                for page in paginator.paginate():
                    for stack in page.get('StackSummaries', []):
                        if stack.get('StackStatus') != 'DELETE_COMPLETE':
                            arn = stack['StackId']  # This is the ARN for CloudFormation stacks
                            service = extract_service_from_arn(arn)
                            resource_id_name = extract_resource_identifier_from_arn(arn)
                            arns_dict.setdefault(service_name, []).append({
                                'arn': arn,
                                'name': resource_id_name,
                                'subclass': service,
                                'region': region,
                                'creation_date': stack.get('CreationTime', 'Unknown').isoformat() if hasattr(stack.get('CreationTime', 'Unknown'), 'isoformat') else str(stack.get('CreationTime', 'Unknown'))
                            })
            except Exception as e:
                if "OptInRequired" not in str(e):
                    print(f"Error listing CloudFormation stacks in {region}: {e}")

        elif service_name == 'apigateway':  # This is for API Gateway v1 (REST APIs)
            try:
                paginator = client.get_paginator('get_rest_apis')
                for page in paginator.paginate():
                    for api in page.get('items', []):
                        api_id = api['id']
                        # Construct ARN for API Gateway v1 REST API
                        arn = f"arn:aws:apigateway:{region}:{account_id}:/restapis/{api_id}"
                        service = extract_service_from_arn(arn)
                        resource_id_name = extract_resource_identifier_from_arn(arn)
                        arns_dict.setdefault(service_name, []).append({
                            'arn': arn,
                            'name': resource_id_name,
                            'subclass': service,
                            'region': region,
                            'creation_date': api.get('createdDate', 'Unknown').isoformat() if hasattr(api.get('createdDate', 'Unknown'), 'isoformat') else str(api.get('createdDate', 'Unknown'))
                        })
            except Exception as e:
                if "OptInRequired" not in str(e):
                    print(f"Error listing API Gateway (v1) REST APIs in {region}: {e}")
        
        # Placeholder for apigatewayv2 (HTTP and WebSocket APIs) if needed in the future
        # elif service_name == 'apigatewayv2':
        #     pass

        elif service_name == 'eks':
            try:
                paginator = client.get_paginator('list_clusters')
                for page in paginator.paginate():
                    for cluster_name_iter in page.get('clusters', []):
                        try:
                            cluster_details = client.describe_cluster(name=cluster_name_iter)
                            cluster_data = cluster_details.get('cluster', {})
                            arn = cluster_data.get('arn')
                            if not arn:
                                continue   # Should always have ARN

                            service = extract_service_from_arn(arn)
                            resource_id_name = extract_resource_identifier_from_arn(arn)
                            arns_dict.setdefault(service_name, []).append({
                                'arn': arn,
                                'name': resource_id_name,
                                'subclass': service,
                                'cluster_name': cluster_data.get('name', cluster_name_iter),
                                'region': region,
                                'endpoint': cluster_data.get('endpoint', 'Unknown'),
                                'version': cluster_data.get('version', 'Unknown'),
                                'creation_date': cluster_data.get('createdAt', 'Unknown').isoformat() if hasattr(cluster_data.get('createdAt', 'Unknown'), 'isoformat') else str(cluster_data.get('createdAt', 'Unknown'))
                            })
                        except Exception as e_detail:
                            print(f"Error getting details for EKS cluster {cluster_name_iter} in {region}: {e_detail}")
                            # Fallback with basic info if describe_cluster fails
                            arn_fallback = f"arn:aws:eks:{region}:{account_id}:cluster/{cluster_name_iter}"
                            service_fallback = extract_service_from_arn(arn_fallback)
                            resource_id_name_fallback = extract_resource_identifier_from_arn(arn_fallback)
                            arns_dict.setdefault(service_name, []).append({
                                'arn': arn_fallback,
                                'name': resource_id_name_fallback,
                                'subclass': service_fallback,
                                'cluster_name': cluster_name_iter,
                                'region': region,
                                'creation_date': 'Unknown'
                            })
            except Exception as e:
                if "OptInRequired" not in str(e):
                    print(f"Error listing EKS clusters in {region}: {e}")

        elif service_name == 'ecs':
            try:  # ECS Clusters
                paginator_clusters = client.get_paginator('list_clusters')
                for page_cluster in paginator_clusters.paginate():
                    cluster_arns_list = page_cluster.get('clusterArns', [])
                    if not cluster_arns_list:
                        continue

                    described_clusters = client.describe_clusters(clusters=cluster_arns_list).get('clusters', [])
                    for cluster_data in described_clusters:
                        cluster_arn = cluster_data.get('clusterArn')
                        if not cluster_arn:
                            continue

                        actual_cluster_name = cluster_data.get('clusterName', 'Unknown')
                        service = extract_service_from_arn(cluster_arn)
                        resource_id_name = extract_resource_identifier_from_arn(cluster_arn)
                        
                        # Optionally, list services and task definitions (can be slow and many API calls)
                        # For this script, we'll keep it simpler and just list cluster info.
                        # Add service_count if desired:
                        # running_tasks_count = cluster_data.get('runningTasksCount', 0)
                        # pending_tasks_count = cluster_data.get('pendingTasksCount', 0)
                        # active_services_count = cluster_data.get('activeServicesCount', 0)

                        arns_dict.setdefault(service_name, []).append({
                            'arn': cluster_arn,
                            'name': resource_id_name,
                            'subclass': service,
                            'region': region,
                            'cluster_name': actual_cluster_name,
                            'status': cluster_data.get('status', 'Unknown'),
                            'creation_date': 'Unknown'  # ECS Clusters don't have a direct creation date via this API
                        })
            except Exception as e:
                if "OptInRequired" not in str(e):
                    print(f"Error listing ECS clusters in {region}: {e}")

        elif service_name == 'ecr':
            try:
                paginator = client.get_paginator('describe_repositories')
                for page in paginator.paginate():
                    for repo in page.get('repositories', []):
                        repo_arn = repo['repositoryArn']
                        service = extract_service_from_arn(repo_arn)
                        resource_id_name = extract_resource_identifier_from_arn(repo_arn)
                        image_count = 0  # Default
                        try:
                            # Count images (can be slow for many images)
                            # For simplicity, we can get the count from list_images if needed,
                            # or just indicate it's not fetched for speed.
                            # list_images_paginator = client.get_paginator('list_images')
                            # for list_page in list_images_paginator.paginate(repositoryName=repo['repositoryName']):
                            #    image_count += len(list_page.get('imageIds', []))
                            # For now, let's skip detailed image count for speed.
                            pass
                        except Exception as img_e:
                            print(f"Warning: Could not count images for ECR repo {repo['repositoryName']}: {img_e}")

                        arns_dict.setdefault(service_name, []).append({
                            'arn': repo_arn,
                            'name': resource_id_name,
                            'subclass': service,
                            'region': region,
                            'repo_name': repo.get('repositoryName', 'Unknown'),
                            'uri': repo.get('repositoryUri', 'Unknown'),
                            'image_count': 'Not_Fetched',  # Or implement counting if needed
                            'creation_date': repo.get('createdAt', 'Unknown').isoformat() if hasattr(repo.get('createdAt', 'Unknown'), 'isoformat') else str(repo.get('createdAt', 'Unknown'))
                        })
            except Exception as e:
                if "OptInRequired" not in str(e):
                    print(f"Error listing ECR repositories in {region}: {e}")

        elif service_name == 'elasticache':
            try:  # ElastiCache Cache Clusters (Memcached or single-node Redis)
                paginator_cc = client.get_paginator('describe_cache_clusters')
                for page_cc in paginator_cc.paginate(ShowCacheNodeInfo=True):  # ShowCacheNodeInfo for endpoint
                    for cluster_node_data in page_cc.get('CacheClusters', []):
                        cluster_id = cluster_node_data['CacheClusterId']
                        # ElastiCache ARNs are constructed
                        arn = f"arn:aws:elasticache:{region}:{account_id}:cluster:{cluster_id}"
                        service = extract_service_from_arn(arn)
                        resource_id_name = extract_resource_identifier_from_arn(arn)
                        
                        endpoint_address = "Unknown"
                        endpoint_port = "Unknown"
                        if cluster_node_data.get('CacheNodes'):
                            # For Memcached, node endpoints are listed. For Redis (non-clustered), it's also here.
                            # Taking the first node's endpoint.
                            first_node = cluster_node_data['CacheNodes'][0]
                            endpoint_address = first_node.get('Endpoint', {}).get('Address', 'Unknown')
                            endpoint_port = first_node.get('Endpoint', {}).get('Port', 'Unknown')
                        
                        full_endpoint = f"{endpoint_address}:{endpoint_port}" if endpoint_address != 'Unknown' and endpoint_port != 'Unknown' else 'Unknown'

                        arns_dict.setdefault('elasticache_cluster', []).append({  # Specific key for cache clusters
                            'arn': arn,
                            'name': resource_id_name,
                            'subclass': service,  # Will be 'elasticache'
                            'item_type': 'cache_cluster',
                            'region': region,
                            'id': cluster_id,
                            'engine': cluster_node_data.get('Engine', 'Unknown'),
                            'status': cluster_node_data.get('CacheClusterStatus', 'Unknown'),
                            'endpoint': full_endpoint,
                            'creation_date': cluster_node_data.get('CacheClusterCreateTime', 'Unknown').isoformat() if hasattr(cluster_node_data.get('CacheClusterCreateTime', 'Unknown'), 'isoformat') else str(cluster_node_data.get('CacheClusterCreateTime', 'Unknown'))
                        })
            except Exception as e_cc:
                if "OptInRequired" not in str(e_cc):
                    print(f"Error listing ElastiCache Cache Clusters in {region}: {e_cc}")

            try:  # ElastiCache Replication Groups (Redis clustered or non-clustered with replication)
                paginator_rg = client.get_paginator('describe_replication_groups')
                for page_rg in paginator_rg.paginate():
                    for repl_group in page_rg.get('ReplicationGroups', []):
                        group_id = repl_group['ReplicationGroupId']
                        # ElastiCache ARNs are constructed
                        arn = f"arn:aws:elasticache:{region}:{account_id}:replicationgroup:{group_id}"
                        service = extract_service_from_arn(arn)
                        resource_id_name = extract_resource_identifier_from_arn(arn)

                        endpoint_address = "Unknown"
                        endpoint_port = "Unknown"
                        # ConfigurationEndpoint is for Redis (cluster mode enabled)
                        # PrimaryEndpoint is for Redis (cluster mode disabled) within NodeGroups
                        if repl_group.get('ConfigurationEndpoint'):
                            endpoint_address = repl_group['ConfigurationEndpoint'].get('Address', 'Unknown')
                            endpoint_port = repl_group['ConfigurationEndpoint'].get('Port', 'Unknown')
                        elif repl_group.get('NodeGroups') and repl_group['NodeGroups'][0].get('PrimaryEndpoint'):
                            primary_ep = repl_group['NodeGroups'][0]['PrimaryEndpoint']
                            endpoint_address = primary_ep.get('Address', 'Unknown')
                            endpoint_port = primary_ep.get('Port', 'Unknown')
                        
                        full_endpoint = f"{endpoint_address}:{endpoint_port}" if endpoint_address != 'Unknown' and endpoint_port != 'Unknown' else 'Unknown'

                        arns_dict.setdefault('elasticache_replication_group', []).append({
                            'arn': arn,
                            'name': resource_id_name,
                            'subclass': service,  # Will be 'elasticache'
                            'item_type': 'replication_group',
                            'region': region,
                            'id': group_id,
                            'description': repl_group.get('Description', 'No description'),
                            'status': repl_group.get('Status', 'Unknown'),
                            'endpoint': full_endpoint,
                            'creation_date': 'Unknown'  # Replication Groups don't have a direct creation date via this API
                        })
            except Exception as e_rg:
                if "OptInRequired" not in str(e_rg):
                    print(f"Error listing ElastiCache Replication Groups in {region}: {e_rg}")

    except botocore.exceptions.ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == "AccessDenied" or "UnauthorizedOperation" in str(e):
            print(f"Access denied for service {service_name} in region {region}. Skipping.")
        elif "OptInRequired" in str(e):
            # Silently ignore opt-in required regions or services not subscribed
            pass
        elif "InvalidClientTokenId" in str(e) or "AuthFailure" in str(e):
            print(f"Authentication error (Invalid credentials or token) for service {service_name} in region {region}. Skipping.")
        elif "EndpointConnectionError" in str(e):
            print(f"Cannot connect to endpoint for service {service_name} in region {region}. Skipping.")
        else:
            print(f"ClientError for service {service_name} in region {region}: {e}. Skipping.")
    except Exception as e:
        print(f"Unexpected error for service {service_name} in region {region}: {e}. Skipping.")


def main():
    """ Main function """
    print("Starting AWS resource ARN scanner across all regions...")
    print("Using credentials from environment variables or default profile.")

    try:
        session = get_session()
        sts_client = session.client('sts')
        account_id = sts_client.get_caller_identity()['Account']
        caller_arn = sts_client.get_caller_identity()['Arn']
        print(f"Connected to AWS Account: {account_id} using identity: {caller_arn}")
    except Exception as e:
        print(f"Error authenticating with AWS: {e}")
        print("Ensure your AWS credentials (e.g., environment variables, shared credentials file, or IAM role) are configured correctly.")
        sys.exit(1)

    regions = get_all_regions()
    if not regions:
        print("No AWS regions found or could be fetched. Exiting.")
        sys.exit(1)
    print(f"Found {len(regions)} available AWS regions for scanning: {', '.join(regions)}")

    services_to_scan = [
        's3', 'ec2', 'rds', 'dynamodb', 'sns', 'iam',
        'apigateway', 'elbv2', 'elb', 'eks', 'ecs', 'ecr'
    ]

# remover lambda, sqs, cloudformation, elasticache

# Originais
# 's3', 'ec2', 'lambda', 'rds', 'dynamodb', 'sns', 'sqs', 'iam', 'cloudformation', 'apigateway', 'elbv2', 'elb', 'eks', 'ecs', 'ecr', 'elasticache'

    print(f"Scanning {len(services_to_scan)} services: {', '.join(services_to_scan)}")

    all_arns_data = {}  # Renamed to avoid conflict with 'all_arns' if used as a variable name elsewhere

    # Use a ThreadPoolExecutor for concurrent API calls
    # Adjust max_workers based on your environment and API rate limits
    # AWS SDKs often handle some level of concurrency and retries internally.
    # Too many workers might lead to throttling.
    max_workers = min(20, len(regions) * len(services_to_scan) // 2 + 1)  # Heuristic
    print(f"Using up to {max_workers} worker threads for scanning.")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {}
        for service_item in services_to_scan:
            if service_item in ['iam', 's3']:  # Global services (S3 list_buckets is global)
                # For S3, we list buckets globally (us-east-1) but then get individual bucket regions.
                # For IAM, all operations are against the global endpoint.
                task_region = 'us-east-1'
                future = executor.submit(collect_resource_arns, service_item, task_region, all_arns_data)
                future_to_task[future] = f"{service_item}@{task_region}"
            else:  # Regional services
                for region_item in regions:
                    future = executor.submit(collect_resource_arns, service_item, region_item, all_arns_data)
                    future_to_task[future] = f"{service_item}@{region_item}"

        total_tasks = len(future_to_task)
        completed_tasks = 0
        print(f"Submitted {total_tasks} tasks to thread pool.")

        for future in concurrent.futures.as_completed(future_to_task):
            task_name = future_to_task[future]
            completed_tasks += 1
            try:
                future.result()  # We call result to raise any exceptions from the thread
                # print(f"Task {task_name} completed successfully. ({completed_tasks}/{total_tasks})")
            except Exception as exc:
                print(f"Task {task_name} generated an exception: {exc}")
            
            if completed_tasks % (total_tasks // 10 if total_tasks > 10 else 1) == 0 or completed_tasks == total_tasks : # Print progress roughly every 10% or on completion
                 print(f"Progress: {completed_tasks}/{total_tasks} tasks processed.")

    total_resources_found = sum(len(resources_list) for resources_list in all_arns_data.values())
    print(f"\nScan complete. Found {total_resources_found} resources across {len(all_arns_data)} service/item categories.")

    # Group resources by region for better display and JSON output
    resources_by_region_output = {}
    for service_key, resources_list_data in all_arns_data.items():
        for resource_item_data in resources_list_data:
            region_val = resource_item_data.get('region', 'global_or_unknown') # Ensure region key exists
            # Initialize region if not present
            resources_by_region_output.setdefault(region_val, {})
            # Initialize service_key under region if not present
            resources_by_region_output[region_val].setdefault(service_key, []).append(resource_item_data)


    print("\n--- AWS Resource Summary (Console Output) ---")
    for region_key_print in sorted(resources_by_region_output.keys()):
        region_resources_data = resources_by_region_output[region_key_print]
        region_total_count = sum(len(svc_resources) for svc_resources in region_resources_data.values())
        print(f"\nREGION: {region_key_print} ({region_total_count} resources)")
        print("-" * 40)
        for service_print_key, resources_print_list in sorted(region_resources_data.items()):
            print(f"  Service/Item: {service_print_key.upper()} ({len(resources_print_list)} found)")
            for resource in sorted(resources_print_list, key=lambda x: x.get('arn', '')):
                print(f"    ARN: {resource.get('arn', 'N/A')}")
                print(f"    Name (from ARN): {resource.get('name', 'N/A')}")
                print(f"    Subclass (Service in ARN): {resource.get('subclass', 'N/A')}")
                if 'item_type' in resource:  # For IAM, ElastiCache etc.
                    print(f"    Item Type: {resource.get('item_type')}")
                print(f"    Created: {resource.get('creation_date', 'N/A')}")

                # Specific fields based on service_print_key (which is the key in all_arns_data)
                if service_print_key == 'ec2':
                    print(f"    Private IP: {resource.get('private_ip', 'N/A')}, Public IP: {resource.get('public_ip', 'N/A')}")
                elif service_print_key == 's3':
                    print(f"    Endpoint: {resource.get('endpoint', 'N/A')}")
                    print(f"    Account: {account_id}")
                # elif service_print_key == 'vpc':
                #     print(f"    CIDR: {resource.get('cidr', 'N/A')}")
                elif service_print_key in ['alb', 'nlb', 'classic_elb']:
                    print(f"    Endpoint: {resource.get('endpoint', 'N/A')}, Scheme: {resource.get('scheme', 'N/A')}")
                elif service_print_key == 'eks':
                    print(f"    Cluster Name: {resource.get('cluster_name', 'N/A')}, Version: {resource.get('version', 'N/A')}, Endpoint: {resource.get('endpoint', 'N/A')}")
                elif service_print_key == 'ecs':
                    print(f"    Cluster Name: {resource.get('cluster_name', 'N/A')}, Status: {resource.get('status', 'N/A')}")
                elif service_print_key == 'ecr':
                    print(f"    Repo Name: {resource.get('repo_name', 'N/A')}, URI: {resource.get('uri', 'N/A')}")
                elif service_print_key in ['elasticache_cluster', 'elasticache_replication_group']:
                    print(f"    ID: {resource.get('id', 'N/A')}, Engine: {resource.get('engine', 'N/A') if 'engine' in resource else 'N/A (RG)'}, Status: {resource.get('status', 'N/A')}, Endpoint: {resource.get('endpoint', 'N/A')}")
                print("    " + "." * 38) # Separator
            print()  # Extra line after each service's resources

    # Save results to JSON files
    current_timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename_all_services = f"aws_resources_all_services_{account_id}_{current_timestamp}.json"
    with open(filename_all_services, 'w') as f:
        json.dump(all_arns_data, f, indent=2, default=str)  # Use all_arns_data which is service-keyed

    filename_by_region = f"aws_resources_by_region_{account_id}_{current_timestamp}.json"
    with open(filename_by_region, 'w') as f:
        json.dump(resources_by_region_output, f, indent=2, default=str)  # Use resources_by_region_output

    print("\nResults saved to:")
    print(f"- {filename_all_services} (organized by service first)")
    print(f"- {filename_by_region} (organized by region first)")
    print("\nScript finished.")


if __name__ == "__main__":
    main()
