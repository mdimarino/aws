#!/usr/bin/env python
"""
Script to list all AWS resource ARNs in an AWS account across all available regions.
Credentials are sourced from environment variables.
"""

import boto3
import botocore
import concurrent.futures
import os
import sys
import json
from datetime import datetime

def get_session():
    """Create a boto3 session using environment variables for credentials."""
    # Use default region initially (will be overridden in region-specific calls)
    return boto3.Session()

def get_all_regions():
    """Get a list of all available AWS regions."""
    try:
        session = get_session()
        ec2_client = session.client('ec2', region_name='us-east-1')  # Use us-east-1 to get regions
        regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
        return regions
    except Exception as e:
        print(f"Error getting AWS regions: {e}")
        print("Falling back to a default list of major AWS regions")
        # Fallback list of major regions if API call fails
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
        # Split the ARN into a maximum of 6 parts. The 6th part (index 5) is the resource identifier.
        parts = arn_string.split(':', 5)
        if len(parts) > 5:
            return parts[5]
        else:
            # This case implies a very short or malformed ARN string.
            # For example, an ARN that doesn't specify a resource but refers to a service/account level.
            # Or S3 ARNs like "arn:aws:s3:::bucket-name", where parts[5] is "bucket-name".
            # If it's truly shorter, it's likely not a resource ARN in the typical sense.
            return "Unknown_Short_Or_Malformed_ARN"
    except Exception as e:
        # print(f"Error parsing ARN '{arn_string}': {e}") # Uncomment for debugging
        return "Unknown_Error_Parsing_ARN"

def collect_resource_arns(service_name, region, arns_dict):
    """Collect ARNs for a specific service in the specified region."""
    try:
        session = get_session()
        client = session.client(service_name, region_name=region)

        def extract_service_from_arn(arn):
            """Extracts the service name from an ARN."""
            parts = arn.split(':')
            if len(parts) >= 3:
                return parts[2]  # The service is the 3rd component
            return 'Unknown'

        # Collection strategies by service
        if service_name == 'elbv2':
            try:
                # Get Application Load Balancers and Network Load Balancers
                response = client.describe_load_balancers()
                for lb in response.get('LoadBalancers', []):
                    lb_type = lb.get('Type', 'unknown').lower()
                    endpoint = lb.get('DNSName', 'Unknown')
                    arn = lb['LoadBalancerArn']
                    service = extract_service_from_arn(arn)
                    resource_id_name = extract_resource_identifier_from_arn(arn) # New name field
                    common_data = {
                        'arn': arn,
                        'name': resource_id_name,
                        'subclass': service,
                        'region': region,
                        'endpoint': endpoint,
                        'scheme': lb.get('Scheme', 'Unknown'),
                        'creation_date': lb.get('CreatedTime', 'Unknown').isoformat() if hasattr(lb.get('CreatedTime', 'Unknown'), 'isoformat') else 'Unknown'
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
                response = client.describe_load_balancers()
                account_id = session.client('sts').get_caller_identity()['Account']
                for lb in response.get('LoadBalancerDescriptions', []):
                    lb_name_val = lb['LoadBalancerName']
                    endpoint = lb.get('DNSName', 'Unknown')
                    arn = f"arn:aws:elasticloadbalancing:{region}:{account_id}:loadbalancer/{lb_name_val}"
                    service = extract_service_from_arn(arn)
                    resource_id_name = extract_resource_identifier_from_arn(arn) # New name field
                    arns_dict.setdefault('classic_elb', []).append({
                        'arn': arn,
                        'name': resource_id_name,
                        'subclass': service,
                        'region': region,
                        'endpoint': endpoint,
                        'scheme': lb.get('Scheme', 'Unknown'),
                        'creation_date': lb.get('CreatedTime', 'Unknown').isoformat() if hasattr(lb.get('CreatedTime', 'Unknown'), 'isoformat') else 'Unknown'
                    })
            except Exception as e:
                if "OptInRequired" not in str(e):
                    print(f"Error listing Classic ELB load balancers in {region}: {e}")

        elif service_name == 's3':
            if region == 'us-east-1':
                try:
                    response = client.list_buckets()
                    for bucket in response['Buckets']:
                        bucket_name_val = bucket['Name']
                        try:
                            bucket_location = client.get_bucket_location(Bucket=bucket_name_val)
                            bucket_region = bucket_location.get('LocationConstraint')
                            if bucket_region is None: bucket_region = 'us-east-1'
                            endpoint = f"https://{bucket_name_val}.s3.{bucket_region}.amazonaws.com" if bucket_region != 'us-east-1' else f"https://{bucket_name_val}.s3.amazonaws.com"
                        except Exception as e:
                            print(f"Error getting location for bucket {bucket_name_val}: {e}")
                            endpoint = f"https://{bucket_name_val}.s3.amazonaws.com"
                        arn = f"arn:aws:s3:::{bucket_name_val}"
                        service = extract_service_from_arn(arn)
                        resource_id_name = extract_resource_identifier_from_arn(arn) # New name field
                        arns_dict.setdefault(service_name, []).append({
                            'arn': arn,
                            'name': resource_id_name,
                            'subclass': service,
                            'region': bucket_region,
                            'endpoint': endpoint,
                            'creation_date': bucket['CreationDate'].isoformat() if 'CreationDate' in bucket else 'Unknown'
                        })
                except Exception as e:
                    print(f"Error listing S3 buckets: {e}")

        elif service_name == 'ec2':
            try:
                response = client.describe_instances()
                for reservation in response.get('Reservations', []):
                    for instance in reservation.get('Instances', []):
                        instance_id = instance['InstanceId']
                        private_ip = instance.get('PrivateIpAddress', 'None')
                        public_ip = instance.get('PublicIpAddress', 'None')
                        arn = f"arn:aws:ec2:{region}:{session.client('sts').get_caller_identity()['Account']}:instance/{instance_id}"
                        service = extract_service_from_arn(arn)
                        resource_id_name = extract_resource_identifier_from_arn(arn) # New name field
                        arns_dict.setdefault(service_name, []).append({
                            'arn': arn,
                            'name': resource_id_name,
                            'subclass': service,
                            'region': region,
                            'private_ip': private_ip,
                            'public_ip': public_ip,
                            'creation_date': instance.get('LaunchTime', 'Unknown').isoformat() if hasattr(instance.get('LaunchTime', 'Unknown'), 'isoformat') else 'Unknown'
                        })
            except Exception as e:
                if "OptInRequired" not in str(e):
                    print(f"Error listing EC2 instances in {region}: {e}")

            try:
                response = client.describe_vpcs()
                for vpc in response.get('Vpcs', []):
                    vpc_id = vpc['VpcId']
                    arn = f"arn:aws:ec2:{region}:{session.client('sts').get_caller_identity()['Account']}:vpc/{vpc_id}"
                    service = extract_service_from_arn(arn) # This will be 'ec2'
                    resource_id_name = extract_resource_identifier_from_arn(arn) # New name field
                    arns_dict.setdefault('vpc', []).append({
                        'arn': arn,
                        'name': resource_id_name,
                        'subclass': service, # Storing 'ec2' as subclass
                        'region': region,
                        'cidr': vpc.get('CidrBlock', 'Unknown'),
                        'creation_date': 'Unknown'
                    })
            except Exception as e:
                if "OptInRequired" not in str(e):
                    print(f"Error listing VPCs in {region}: {e}")

        elif service_name == 'lambda':
            try:
                response = client.list_functions()
                for function in response.get('Functions', []):
                    arn = function['FunctionArn']
                    service = extract_service_from_arn(arn)
                    resource_id_name = extract_resource_identifier_from_arn(arn) # New name field
                    arns_dict.setdefault(service_name, []).append({
                        'arn': arn,
                        'name': resource_id_name,
                        'subclass': service,
                        'region': region,
                        'creation_date': function.get('LastModified', 'Unknown')
                    })
            except Exception as e:
                if "OptInRequired" not in str(e):
                    print(f"Error listing Lambda functions in {region}: {e}")

        elif service_name == 'rds':
            try:
                response = client.describe_db_instances()
                for instance in response.get('DBInstances', []):
                    arn = instance['DBInstanceArn']
                    service = extract_service_from_arn(arn)
                    resource_id_name = extract_resource_identifier_from_arn(arn) # New name field
                    arns_dict.setdefault(service_name, []).append({
                        'arn': arn,
                        'name': resource_id_name,
                        'subclass': service,
                        'region': region,
                        'creation_date': instance.get('InstanceCreateTime', 'Unknown').isoformat() if hasattr(instance.get('InstanceCreateTime', 'Unknown'), 'isoformat') else 'Unknown'
                    })
            except Exception as e:
                if "OptInRequired" not in str(e):
                    print(f"Error listing RDS instances in {region}: {e}")

        elif service_name == 'dynamodb':
            try:
                response = client.list_tables()
                account_id = session.client('sts').get_caller_identity()['Account']
                for table_name_val in response.get('TableNames', []):
                    arn = f"arn:aws:dynamodb:{region}:{account_id}:table/{table_name_val}"
                    try:
                        table_details = client.describe_table(TableName=table_name_val)
                        creation_date = table_details['Table'].get('CreationDateTime', 'Unknown')
                        if hasattr(creation_date, 'isoformat'): creation_date = creation_date.isoformat()
                    except Exception: creation_date = 'Unknown'
                    service = extract_service_from_arn(arn)
                    resource_id_name = extract_resource_identifier_from_arn(arn) # New name field
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
                response = client.list_topics()
                for topic in response.get('Topics', []):
                    arn = topic['TopicArn']
                    service = extract_service_from_arn(arn)
                    resource_id_name = extract_resource_identifier_from_arn(arn) # New name field
                    arns_dict.setdefault(service_name, []).append({
                        'arn': arn,
                        'name': resource_id_name,
                        'subclass': service,
                        'region': region,
                        'creation_date': 'Unknown'
                    })
            except Exception as e:
                if "OptInRequired" not in str(e):
                    print(f"Error listing SNS topics in {region}: {e}")

        elif service_name == 'sqs':
            try:
                response = client.list_queues()
                for queue_url in response.get('QueueUrls', []):
                    queue_attrs = client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['QueueArn', 'CreatedTimestamp'])
                    arn = queue_attrs['Attributes']['QueueArn']
                    creation_timestamp = queue_attrs['Attributes'].get('CreatedTimestamp', 'Unknown')
                    creation_date = datetime.fromtimestamp(int(creation_timestamp)).isoformat() if creation_timestamp != 'Unknown' else 'Unknown'
                    service = extract_service_from_arn(arn)
                    resource_id_name = extract_resource_identifier_from_arn(arn) # New name field
                    arns_dict.setdefault(service_name, []).append({
                        'arn': arn,
                        'name': resource_id_name,
                        'subclass': service,
                        'region': region,
                        'creation_date': creation_date
                    })
            except Exception as e:
                if "OptInRequired" not in str(e):
                    print(f"Error listing SQS queues in {region}: {e}")

        elif service_name == 'iam':
            if region == 'us-east-1':
                try:
                    for item_type, list_method, items_key, date_key in [
                        ('role', client.list_roles, 'Roles', 'CreateDate'),
                        ('user', client.list_users, 'Users', 'CreateDate'),
                        ('policy', lambda: client.list_policies(Scope='Local'), 'Policies', 'CreateDate') # Lambda for list_policies
                    ]:
                        paginator = client.get_paginator(list_method.__name__.replace('list_', '')) if item_type != 'policy' else None # No paginator for list_policies with lambda
                        
                        if item_type == 'policy': # Handle policy specially due to scope
                            response_iterator = [list_method()]
                        else:
                            response_iterator = paginator.paginate() if paginator else [list_method()]


                        for page in response_iterator:
                            for item in page.get(items_key, []):
                                arn = item['Arn']
                                service = extract_service_from_arn(arn)
                                resource_id_name = extract_resource_identifier_from_arn(arn) # New name field
                                arns_dict.setdefault(service_name, []).append({
                                    'arn': arn,
                                    'name': resource_id_name,
                                    'subclass': service, # Will be 'iam'
                                    'item_type': item_type, # Differentiate between role/user/policy
                                    'region': 'global',
                                    'creation_date': item.get(date_key, 'Unknown').isoformat() if hasattr(item.get(date_key, 'Unknown'), 'isoformat') else 'Unknown'
                                })
                except Exception as e:
                    print(e)
                    print(f"Error listing IAM resources: {e}")


        elif service_name == 'cloudformation':
            try:
                response = client.list_stacks()
                for stack in response.get('StackSummaries', []):
                    if stack['StackStatus'] != 'DELETE_COMPLETE':
                        arn = stack['StackId']
                        service = extract_service_from_arn(arn)
                        resource_id_name = extract_resource_identifier_from_arn(arn) # New name field
                        arns_dict.setdefault(service_name, []).append({
                            'arn': arn,
                            'name': resource_id_name,
                            'subclass': service,
                            'region': region,
                            'creation_date': stack.get('CreationTime', 'Unknown').isoformat() if hasattr(stack.get('CreationTime', 'Unknown'), 'isoformat') else 'Unknown'
                        })
            except Exception as e:
                if "OptInRequired" not in str(e):
                    print(f"Error listing CloudFormation stacks in {region}: {e}")

        elif service_name == 'apigateway':
            try:
                response = client.get_rest_apis()
                account_id = session.client('sts').get_caller_identity()['Account']
                for api in response.get('items', []):
                    # Construct ARN carefully for API Gateway, as it can vary.
                    # The /restapis/{api-id} is standard.
                    arn = f"arn:aws:apigateway:{region}:{account_id}:/restapis/{api['id']}"
                    service = extract_service_from_arn(arn)
                    resource_id_name = extract_resource_identifier_from_arn(arn) # New name field
                    arns_dict.setdefault(service_name, []).append({
                        'arn': arn,
                        'name': resource_id_name,
                        'subclass': service,
                        'region': region,
                        'creation_date': api.get('createdDate', 'Unknown').isoformat() if hasattr(api.get('createdDate', 'Unknown'), 'isoformat') else 'Unknown'
                    })
            except Exception as e:
                if "OptInRequired" not in str(e):
                    print(f"Error listing API Gateway APIs in {region}: {e}")

        elif service_name == 'eks':
            try:
                response = client.list_clusters()
                for cluster_name_iter in response.get('clusters', []):
                    try:
                        cluster_details = client.describe_cluster(name=cluster_name_iter)
                        cluster_data = cluster_details.get('cluster', {})
                        arn = cluster_data.get('arn')
                        service = extract_service_from_arn(arn)
                        resource_id_name = extract_resource_identifier_from_arn(arn) # New name field
                        endpoint = cluster_data.get('endpoint', 'Unknown')
                        version = cluster_data.get('version', 'Unknown')
                        actual_cluster_name = cluster_data.get('name', cluster_name_iter)
                        arns_dict.setdefault(service_name, []).append({
                            'arn': arn,
                            'name': resource_id_name,
                            'subclass': service,
                            'cluster_name': actual_cluster_name,
                            'region': region,
                            'endpoint': endpoint,
                            'version': version,
                            'creation_date': cluster_data.get('createdAt', 'Unknown').isoformat() if hasattr(cluster_data.get('createdAt', 'Unknown'), 'isoformat') else 'Unknown'
                        })
                    except Exception as e_detail: # Renamed to avoid conflict
                        print(f"Error getting details for EKS cluster {cluster_name_iter} in {region}: {e_detail}")
                        account_id = session.client('sts').get_caller_identity()['Account']
                        arn = f"arn:aws:eks:{region}:{account_id}:cluster/{cluster_name_iter}"
                        service = extract_service_from_arn(arn)
                        resource_id_name = extract_resource_identifier_from_arn(arn) # New name field
                        arns_dict.setdefault(service_name, []).append({
                            'arn': arn,
                            'name': resource_id_name,
                            'subclass': service,
                            'cluster_name': cluster_name_iter,
                            'region': region,
                            'creation_date': 'Unknown'
                        })
            except Exception as e:
                if "OptInRequired" not in str(e):
                    print(f"Error listing EKS clusters in {region}: {e}")

        elif service_name == 'ecs':
            try:
                response = client.list_clusters()
                for cluster_arn in response.get('clusterArns', []):
                    try:
                        cluster_details = client.describe_clusters(clusters=[cluster_arn])
                        if cluster_details.get('clusters'):
                            cluster_data = cluster_details['clusters'][0]
                            actual_cluster_name = cluster_data.get('clusterName', 'Unknown')
                            services_list = []
                            try:
                                service_response = client.list_services(cluster=cluster_arn)
                                for service_arn_item in service_response.get('serviceArns', []):
                                    services_list.append(service_arn_item)
                            except Exception: pass
                            task_defs = set()
                            try:
                                if services_list:
                                    service_details = client.describe_services(cluster=cluster_arn, services=services_list[:10])
                                    for service_item_data in service_details.get('services', []): # Renamed
                                        if 'taskDefinition' in service_item_data: task_defs.add(service_item_data['taskDefinition'])
                            except Exception: pass
                            service = extract_service_from_arn(cluster_arn)
                            resource_id_name = extract_resource_identifier_from_arn(cluster_arn) # New name field
                            arns_dict.setdefault(service_name, []).append({
                                'arn': cluster_arn,
                                'name': resource_id_name,
                                'subclass': service,
                                'region': region,
                                'cluster_name': actual_cluster_name,
                                'service_count': len(services_list),
                                'services': services_list[:5] if services_list else [],
                                'task_definitions': list(task_defs)[:5] if task_defs else [],
                                'creation_date': 'Unknown'
                            })
                    except Exception as e_detail: # Renamed
                        print(f"Error getting details for ECS cluster {cluster_arn} in {region}: {e_detail}")
            except Exception as e:
                if "OptInRequired" not in str(e):
                    print(f"Error listing ECS clusters in {region}: {e}")

        elif service_name == 'ecr':
            try:
                response = client.describe_repositories()
                for repo in response.get('repositories', []):
                    repo_arn = repo['repositoryArn']
                    actual_repo_name = repo['repositoryName']
                    repo_uri = repo['repositoryUri']
                    image_count = 0
                    try:
                        paginator = client.get_paginator('describe_images')
                        for page in paginator.paginate(repositoryName=actual_repo_name):
                            image_count += len(page.get('imageDetails', []))
                    except Exception: pass
                    service = extract_service_from_arn(repo_arn)
                    resource_id_name = extract_resource_identifier_from_arn(repo_arn) # New name field
                    arns_dict.setdefault(service_name, []).append({
                        'arn': repo_arn,
                        'name': resource_id_name,
                        'subclass': service,
                        'region': region,
                        'repo_name': actual_repo_name,
                        'uri': repo_uri,
                        'image_count': image_count,
                        'creation_date': repo.get('createdAt', 'Unknown').isoformat() if hasattr(repo.get('createdAt', 'Unknown'), 'isoformat') else 'Unknown'
                    })
            except Exception as e:
                if "OptInRequired" not in str(e):
                    print(f"Error listing ECR repositories in {region}: {e}")

        elif service_name == 'elasticache':
            try:
                response = client.describe_cache_clusters()
                account_id = session.client('sts').get_caller_identity()['Account']
                for cluster_node_data in response.get('CacheClusters', []):
                    cluster_id = cluster_node_data['CacheClusterId']
                    engine = cluster_node_data.get('Engine', 'Unknown')
                    status = cluster_node_data.get('CacheClusterStatus', 'Unknown')
                    endpoint = 'Unknown'
                    if 'ConfigurationEndpoint' in cluster_node_data and cluster_node_data['ConfigurationEndpoint']:
                        endpoint = f"{cluster_node_data['ConfigurationEndpoint']['Address']}:{cluster_node_data['ConfigurationEndpoint']['Port']}"
                    elif 'CacheNodes' in cluster_node_data and cluster_node_data['CacheNodes']:
                        node = cluster_node_data['CacheNodes'][0]
                        if 'Endpoint' in node: endpoint = f"{node['Endpoint']['Address']}:{node['Endpoint']['Port']}"
                    arn = f"arn:aws:elasticache:{region}:{account_id}:cluster:{cluster_id}"
                    service = extract_service_from_arn(arn)
                    resource_id_name = extract_resource_identifier_from_arn(arn) # New name field
                    arns_dict.setdefault(service_name, []).append({ # Using 'elasticache' as key for individual clusters
                        'arn': arn,
                        'name': resource_id_name,
                        'subclass': service,
                        'region': region,
                        'id': cluster_id,
                        'engine': engine,
                        'status': status,
                        'endpoint': endpoint,
                        'creation_date': cluster_node_data.get('CacheClusterCreateTime', 'Unknown').isoformat() if hasattr(cluster_node_data.get('CacheClusterCreateTime', 'Unknown'), 'isoformat') else 'Unknown'
                    })
                try:
                    response_repl = client.describe_replication_groups() # Renamed
                    for repl_group in response_repl.get('ReplicationGroups', []):
                        group_id = repl_group['ReplicationGroupId']
                        description = repl_group.get('Description', 'No description')
                        status = repl_group.get('Status', 'Unknown')
                        endpoint = 'Unknown'
                        if 'ConfigurationEndpoint' in repl_group and repl_group['ConfigurationEndpoint']:
                            endpoint = f"{repl_group['ConfigurationEndpoint']['Address']}:{repl_group['ConfigurationEndpoint']['Port']}"
                        elif 'NodeGroups' in repl_group and repl_group['NodeGroups']:
                            primary_endpoint_data = repl_group['NodeGroups'][0].get('PrimaryEndpoint', {})
                            if primary_endpoint_data: endpoint = f"{primary_endpoint_data.get('Address', 'Unknown')}:{primary_endpoint_data.get('Port', 'Unknown')}"
                        arn = f"arn:aws:elasticache:{region}:{account_id}:replicationgroup:{group_id}"
                        service = extract_service_from_arn(arn)
                        resource_id_name = extract_resource_identifier_from_arn(arn) # New name field
                        arns_dict.setdefault('elasticache_replication_group', []).append({
                            'arn': arn,
                            'name': resource_id_name,
                            'subclass': service,
                            'region': region,
                            'id': group_id,
                            'description': description,
                            'status': status,
                            'endpoint': endpoint,
                            'creation_date': 'Unknown'
                        })
                except Exception as e_repl: # Renamed
                    if "OptInRequired" not in str(e_repl):
                        print(f"Error listing ElastiCache replication groups in {region}: {e_repl}")
            except Exception as e:
                if "OptInRequired" not in str(e):
                    print(f"Error listing ElastiCache clusters in {region}: {e}")

    except botocore.exceptions.ClientError as e:
        if "AccessDenied" in str(e) or "UnauthorizedOperation" in str(e): print(f"Access denied for service {service_name} in region {region}")
        elif "OptInRequired" in str(e): pass
        elif "InvalidClientTokenId" in str(e): print(f"Invalid credentials for service {service_name} in region {region}")
        elif "EndpointConnectionError" in str(e): print(f"Cannot connect to endpoint for service {service_name} in region {region}")
        else: print(f"Error for service {service_name} in region {region}: {e}")
    except Exception as e:
        print(f"Unexpected error for service {service_name} in region {region}: {e}")


def main():
    print("Starting AWS resource ARN scanner across all regions...")
    print("Using credentials from environment variables")

    try:
        session = get_session()
        account_id = session.client('sts').get_caller_identity()['Account']
        print(f"Connected to AWS Account: {account_id}")
    except Exception as e:
        print(f"Error authenticating with AWS: {e}")
        print("Make sure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables are set properly")
        sys.exit(1)

    regions = get_all_regions()
    print(f"Found {len(regions)} available AWS regions: {', '.join(regions)}")

    services_to_scan = [
        's3', 'ec2', 'lambda', 'rds', 'dynamodb', 'sns', 'sqs', 'iam',
        'cloudformation', 'apigateway', 'elbv2', 'elb', 'eks', 'ecs', 'ecr', 'elasticache'
    ]
    print(f"Scanning {len(services_to_scan)} services across {len(regions)} regions...")

    all_arns = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = []
        for service_item in services_to_scan:
            if service_item in ['iam', 's3']: # Global services (S3 list is global)
                futures.append(executor.submit(collect_resource_arns, service_item, 'us-east-1', all_arns))
            else:
                for region_item in regions:
                    futures.append(executor.submit(collect_resource_arns, service_item, region_item, all_arns))
        
        total_tasks = len(futures)
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e_future: # Renamed
                print(f"Error in thread execution: {e_future}")
            completed += 1
            if completed % 10 == 0 or completed == total_tasks:
                print(f"Progress: {completed}/{total_tasks} tasks completed")

    total_resources = sum(len(resources_list) for resources_list in all_arns.values())
    print(f"\nFound {total_resources} resources across {len(all_arns)} services in {len(regions)} regions")

    resources_by_region = {}
    for service_key, resources_list_data in all_arns.items(): # Renamed
        for resource_item_data in resources_list_data: # Renamed
            region_val = resource_item_data['region']
            resources_by_region.setdefault(region_val, {}).setdefault(service_key, []).append(resource_item_data)

    print("\nAWS Resource ARNs by Region:")
    print("==========================")
    for region_key in sorted(resources_by_region.keys()):
        region_resources = resources_by_region[region_key]
        region_total = sum(len(svc_resources) for svc_resources in region_resources.values())
        print(f"\nREGION: {region_key} ({region_total} resources)")
        print("=" * 50)
        for service_print_key, resources_print_list in sorted(region_resources.items()):
            print(f"\n  {service_print_key.upper()} ({len(resources_print_list)} resources):")
            for resource in sorted(resources_print_list, key=lambda x: x['arn']):
                print(f"    ARN: {resource['arn']}")
                # Display the new 'name' field (resource identifier from ARN) in console output
                print(f"    Name (from ARN): {resource.get('name', 'Unknown')}") 
                print(f"    Subclass: {resource.get('subclass', 'Unknown')}")
                print(f"    Created: {resource.get('creation_date', 'Unknown')}")

                # Additional info for specific resource types (using service_print_key for clarity)
                if service_print_key == 'ec2':
                    print(f"    Private IP: {resource.get('private_ip', 'None')}")
                    print(f"    Public IP: {resource.get('public_ip', 'None')}")
                elif service_print_key == 's3':
                    print(f"    Endpoint: {resource.get('endpoint', 'Unknown')}")
                elif service_print_key == 'vpc':
                    print(f"    CIDR Block: {resource.get('cidr', 'Unknown')}")
                elif service_print_key in ['alb', 'nlb', 'classic_elb']:
                    print(f"    Endpoint: {resource.get('endpoint', 'Unknown')}")
                    print(f"    Scheme: {resource.get('scheme', 'Unknown')}")
                elif service_print_key == 'eks':
                    print(f"    Cluster Name: {resource.get('cluster_name', 'Unknown')}")
                    print(f"    Endpoint: {resource.get('endpoint', 'Unknown')}")
                    print(f"    Version: {resource.get('version', 'Unknown')}")
                elif service_print_key == 'ecs':
                    print(f"    Cluster Name: {resource.get('cluster_name', 'Unknown')}")
                    print(f"    Service Count: {resource.get('service_count', 0)}")
                    if resource.get('services'): print(f"    Sample Services: {', '.join(s.split('/')[-1] for s in resource.get('services', []))}")
                elif service_print_key == 'ecr':
                    print(f"    Repository Name: {resource.get('repo_name', 'Unknown')}")
                    print(f"    URI: {resource.get('uri', 'Unknown')}")
                    print(f"    Image Count: {resource.get('image_count', 0)}")
                elif service_print_key == 'elasticache': # For individual Cache Clusters
                    print(f"    ID: {resource.get('id', 'Unknown')}")
                    print(f"    Engine: {resource.get('engine', 'Unknown')}")
                    print(f"    Status: {resource.get('status', 'Unknown')}")
                    print(f"    Endpoint: {resource.get('endpoint', 'Unknown')}")
                elif service_print_key == 'elasticache_replication_group': # For Replication Groups
                    print(f"    ID: {resource.get('id', 'Unknown')}")
                    print(f"    Description: {resource.get('description', 'Unknown')}")
                    print(f"    Status: {resource.get('status', 'Unknown')}")
                    print(f"    Endpoint: {resource.get('endpoint', 'Unknown')}")
                elif service_print_key == 'iam':
                     print(f"    Item Type: {resource.get('item_type', 'Unknown')}")


                print("    " + "-" * 48)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename_all = f"aws_resources_all_regions_{account_id}_{timestamp}.json" # Renamed
    with open(filename_all, 'w') as f:
        json.dump(all_arns, f, indent=2, default=str)

    region_filename = f"aws_resources_by_region_{account_id}_{timestamp}.json"
    with open(region_filename, 'w') as f:
        json.dump(resources_by_region, f, indent=2, default=str)

    print(f"\nResults saved to:")
    print(f"- {filename_all} (service-based organization)")
    print(f"- {region_filename} (region-based organization)")

if __name__ == "__main__":
    main()
