#!/usr/bin/env python
"""
Script to list all AWS resource ARNs in an AWS account for the specified region.
Credentials and region are sourced from environment variables.
"""

import boto3
import botocore
import concurrent.futures
import os
import sys
import json
from datetime import datetime

def get_session():
    """Create a boto3 session using environment variables for credentials and region."""
    # Explicitly get region from AWS_REGION environment variable
    region = os.environ.get('AWS_REGION')
    if not region:
        print("AWS_REGION environment variable is not set. Please set it and try again.")
        sys.exit(1)
    
    return boto3.Session(region_name=region)

# Function removed as we're only using the region from environment variables

def collect_resource_arns(service_name, region, arns_dict):
    """Collect ARNs for a specific service in the specified region."""
    try:
        session = get_session()
        client = session.client(service_name, region_name=region)
        
        # Collection strategies by service
        if service_name == 'elbv2':
            try:
                # Get Application Load Balancers and Network Load Balancers
                response = client.describe_load_balancers()
                for lb in response.get('LoadBalancers', []):
                    lb_type = lb.get('Type', 'unknown').lower()
                    # Get DNS name (endpoint)
                    endpoint = lb.get('DNSName', 'Unknown')
                    
                    if lb_type == 'application':
                        arns_dict.setdefault('alb', []).append({
                            'arn': lb['LoadBalancerArn'],
                            'region': region,
                            'endpoint': endpoint,
                            'scheme': lb.get('Scheme', 'Unknown'),
                            'creation_date': lb.get('CreatedTime', 'Unknown').isoformat() if hasattr(lb.get('CreatedTime', 'Unknown'), 'isoformat') else 'Unknown'
                        })
                    elif lb_type == 'network':
                        arns_dict.setdefault('nlb', []).append({
                            'arn': lb['LoadBalancerArn'],
                            'region': region,
                            'endpoint': endpoint,
                            'scheme': lb.get('Scheme', 'Unknown'),
                            'creation_date': lb.get('CreatedTime', 'Unknown').isoformat() if hasattr(lb.get('CreatedTime', 'Unknown'), 'isoformat') else 'Unknown'
                        })
            except Exception as e:
                print(f"Error listing ELBv2 load balancers in {region}: {e}")
                
        elif service_name == 'elb':
            try:
                # Get Classic Load Balancers
                response = client.describe_load_balancers()
                account_id = session.client('sts').get_caller_identity()['Account']
                for lb in response.get('LoadBalancerDescriptions', []):
                    # Classic ELB doesn't return ARN directly, so we construct it
                    lb_name = lb['LoadBalancerName']
                    # Get DNS name (endpoint)
                    endpoint = lb.get('DNSName', 'Unknown')
                    
                    arn = f"arn:aws:elasticloadbalancing:{region}:{account_id}:loadbalancer/{lb_name}"
                    arns_dict.setdefault('classic_elb', []).append({
                        'arn': arn,
                        'region': region,
                        'endpoint': endpoint,
                        'scheme': lb.get('Scheme', 'Unknown'),
                        'creation_date': lb.get('CreatedTime', 'Unknown').isoformat() if hasattr(lb.get('CreatedTime', 'Unknown'), 'isoformat') else 'Unknown'
                    })
            except Exception as e:
                print(f"Error listing Classic ELB load balancers in {region}: {e}")
        
        elif service_name == 's3':
            try:
                response = client.list_buckets()
                for bucket in response['Buckets']:
                    bucket_name = bucket['Name']
                    # Get bucket region to construct correct endpoint
                    try:
                        bucket_location = client.get_bucket_location(Bucket=bucket_name)
                        bucket_region = bucket_location.get('LocationConstraint')
                        
                        # If LocationConstraint is None, it's us-east-1
                        if bucket_region is None:
                            bucket_region = 'us-east-1'
                        
                        # Construct the proper endpoint based on region
                        if bucket_region == 'us-east-1':
                            endpoint = f"https://{bucket_name}.s3.amazonaws.com"
                        else:
                            endpoint = f"https://{bucket_name}.s3.{bucket_region}.amazonaws.com"
                            
                    except Exception as e:
                        print(f"Error getting location for bucket {bucket_name}: {e}")
                        endpoint = f"https://{bucket_name}.s3.amazonaws.com"  # Default endpoint format
                    
                    arn = f"arn:aws:s3:::{bucket_name}"
                    arns_dict.setdefault(service_name, []).append({
                        'arn': arn,
                        'region': region,
                        'endpoint': endpoint,
                        'creation_date': bucket['CreationDate'].isoformat() if 'CreationDate' in bucket else 'Unknown'
                    })
            except Exception as e:
                print(f"Error listing S3 buckets: {e}")

        elif service_name == 'ec2':
            # Get EC2 instances
            try:
                response = client.describe_instances()
                for reservation in response.get('Reservations', []):
                    for instance in reservation.get('Instances', []):
                        instance_id = instance['InstanceId']
                        
                        # Get private IP (always exists for running instances)
                        private_ip = instance.get('PrivateIpAddress', 'None')
                        
                        # Get public IP (may not exist)
                        public_ip = instance.get('PublicIpAddress', 'None')
                        
                        arn = f"arn:aws:ec2:{region}:{session.client('sts').get_caller_identity()['Account']}:instance/{instance_id}"
                        arns_dict.setdefault(service_name, []).append({
                            'arn': arn,
                            'region': region,
                            'private_ip': private_ip,
                            'public_ip': public_ip,
                            'creation_date': instance.get('LaunchTime', 'Unknown').isoformat() if hasattr(instance.get('LaunchTime', 'Unknown'), 'isoformat') else 'Unknown'
                        })
            except Exception as e:
                print(f"Error listing EC2 instances in {region}: {e}")
                
            # Get VPCs
            try:
                response = client.describe_vpcs()
                for vpc in response.get('Vpcs', []):
                    vpc_id = vpc['VpcId']
                    arn = f"arn:aws:ec2:{region}:{session.client('sts').get_caller_identity()['Account']}:vpc/{vpc_id}"
                    arns_dict.setdefault('vpc', []).append({
                        'arn': arn,
                        'region': region,
                        'cidr': vpc.get('CidrBlock', 'Unknown'),
                        'creation_date': 'Unknown'  # EC2 VPCs don't expose creation date directly
                    })
            except Exception as e:
                print(f"Error listing VPCs in {region}: {e}")

        elif service_name == 'lambda':
            try:
                response = client.list_functions()
                for function in response.get('Functions', []):
                    arns_dict.setdefault(service_name, []).append({
                        'arn': function['FunctionArn'],
                        'region': region,
                        'creation_date': function.get('LastModified', 'Unknown')
                    })
            except Exception as e:
                print(f"Error listing Lambda functions in {region}: {e}")

        elif service_name == 'rds':
            try:
                response = client.describe_db_instances()
                for instance in response.get('DBInstances', []):
                    arns_dict.setdefault(service_name, []).append({
                        'arn': instance['DBInstanceArn'],
                        'region': region,
                        'creation_date': instance.get('InstanceCreateTime', 'Unknown').isoformat() if hasattr(instance.get('InstanceCreateTime', 'Unknown'), 'isoformat') else 'Unknown'
                    })
            except Exception as e:
                print(f"Error listing RDS instances in {region}: {e}")

        elif service_name == 'dynamodb':
            try:
                response = client.list_tables()
                account_id = session.client('sts').get_caller_identity()['Account']
                for table in response.get('TableNames', []):
                    arn = f"arn:aws:dynamodb:{region}:{account_id}:table/{table}"
                    # Get table details for creation date
                    try:
                        table_details = client.describe_table(TableName=table)
                        creation_date = table_details['Table'].get('CreationDateTime', 'Unknown')
                        if hasattr(creation_date, 'isoformat'):
                            creation_date = creation_date.isoformat()
                    except Exception:
                        creation_date = 'Unknown'
                        
                    arns_dict.setdefault(service_name, []).append({
                        'arn': arn,
                        'region': region,
                        'creation_date': creation_date
                    })
            except Exception as e:
                print(f"Error listing DynamoDB tables in {region}: {e}")

        elif service_name == 'sns':
            try:
                response = client.list_topics()
                for topic in response.get('Topics', []):
                    arns_dict.setdefault(service_name, []).append({
                        'arn': topic['TopicArn'],
                        'region': region,
                        'creation_date': 'Unknown'  # SNS topics don't expose creation date directly
                    })
            except Exception as e:
                print(f"Error listing SNS topics in {region}: {e}")

        elif service_name == 'sqs':
            try:
                response = client.list_queues()
                for queue_url in response.get('QueueUrls', []):
                    queue_attrs = client.get_queue_attributes(
                        QueueUrl=queue_url,
                        AttributeNames=['QueueArn', 'CreatedTimestamp']
                    )
                    arn = queue_attrs['Attributes']['QueueArn']
                    creation_timestamp = queue_attrs['Attributes'].get('CreatedTimestamp', 'Unknown')
                    if creation_timestamp != 'Unknown':
                        creation_date = datetime.fromtimestamp(int(creation_timestamp)).isoformat()
                    else:
                        creation_date = 'Unknown'
                    
                    arns_dict.setdefault(service_name, []).append({
                        'arn': arn,
                        'region': region,
                        'creation_date': creation_date
                    })
            except Exception as e:
                print(f"Error listing SQS queues in {region}: {e}")

        elif service_name == 'iam':
            # IAM is global, so we only need to check in one region
            if region == session.region_name:
                try:
                    # Get roles
                    response = client.list_roles()
                    for role in response.get('Roles', []):
                        arns_dict.setdefault(service_name, []).append({
                            'arn': role['Arn'],
                            'region': 'global',
                            'creation_date': role.get('CreateDate', 'Unknown').isoformat() if hasattr(role.get('CreateDate', 'Unknown'), 'isoformat') else 'Unknown'
                        })
                    
                    # Get users
                    response = client.list_users()
                    for user in response.get('Users', []):
                        arns_dict.setdefault(service_name, []).append({
                            'arn': user['Arn'],
                            'region': 'global',
                            'creation_date': user.get('CreateDate', 'Unknown').isoformat() if hasattr(user.get('CreateDate', 'Unknown'), 'isoformat') else 'Unknown'
                        })
                    
                    # Get policies
                    response = client.list_policies(Scope='Local')  # Only customer managed policies
                    for policy in response.get('Policies', []):
                        arns_dict.setdefault(service_name, []).append({
                            'arn': policy['Arn'],
                            'region': 'global',
                            'creation_date': policy.get('CreateDate', 'Unknown').isoformat() if hasattr(policy.get('CreateDate', 'Unknown'), 'isoformat') else 'Unknown'
                        })
                except Exception as e:
                    print(f"Error listing IAM resources: {e}")
        
        elif service_name == 'cloudformation':
            try:
                response = client.list_stacks()
                for stack in response.get('StackSummaries', []):
                    if stack['StackStatus'] != 'DELETE_COMPLETE':
                        arns_dict.setdefault(service_name, []).append({
                            'arn': stack['StackId'],
                            'region': region,
                            'creation_date': stack.get('CreationTime', 'Unknown').isoformat() if hasattr(stack.get('CreationTime', 'Unknown'), 'isoformat') else 'Unknown'
                        })
            except Exception as e:
                print(f"Error listing CloudFormation stacks in {region}: {e}")
        
        elif service_name == 'apigateway':
            try:
                response = client.get_rest_apis()
                account_id = session.client('sts').get_caller_identity()['Account']
                for api in response.get('items', []):
                    arn = f"arn:aws:apigateway:{region}:{account_id}::/restapis/{api['id']}"
                    arns_dict.setdefault(service_name, []).append({
                        'arn': arn,
                        'region': region,
                        'creation_date': api.get('createdDate', 'Unknown').isoformat() if hasattr(api.get('createdDate', 'Unknown'), 'isoformat') else 'Unknown'
                    })
            except Exception as e:
                print(f"Error listing API Gateway APIs in {region}: {e}")

        # Add more services as needed
                
    except botocore.exceptions.ClientError as e:
        if "AccessDenied" in str(e) or "UnauthorizedOperation" in str(e):
            print(f"Access denied for service {service_name} in region {region}")
        elif "OptInRequired" in str(e):
            print(f"Region {region} requires opt-in for service {service_name}")
        elif "InvalidClientTokenId" in str(e):
            print(f"Invalid credentials for service {service_name} in region {region}")
        elif "EndpointConnectionError" in str(e):
            print(f"Cannot connect to endpoint for service {service_name} in region {region}")
        else:
            print(f"Error for service {service_name} in region {region}: {e}")
    except Exception as e:
        print(f"Unexpected error for service {service_name} in region {region}: {e}")

def main():
    print("Starting AWS resource ARN scanner...")
    print("Using credentials and region from environment variables")
    
    # Get region from environment variable
    region = os.environ.get('AWS_REGION')
    if not region:
        print("AWS_REGION environment variable is not set. Please set it and try again.")
        sys.exit(1)
    
    print(f"Using region: {region}")
    
    # Check if AWS credentials are available
    try:
        session = get_session()
        account_id = session.client('sts').get_caller_identity()['Account']
        print(f"Connected to AWS Account: {account_id}")
    except Exception as e:
        print(f"Error authenticating with AWS: {e}")
        print("Make sure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables are set properly")
        sys.exit(1)
    
    # Services to scan - add/remove services as needed
    services = [
        's3',          # Global service but region affects endpoint
        'ec2',
        'lambda',
        'rds',
        'dynamodb',
        'sns',
        'sqs',
        'iam',         # Global service
        'cloudformation',
        'apigateway',
        'elbv2',       # For Application and Network Load Balancers
        'elb'          # For Classic Load Balancers
        # Add more services as needed
    ]
    
    print(f"Scanning {len(services)} services in region {region}...")
    
    all_arns = {}
    
    # Use ThreadPoolExecutor to parallelize the API calls
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for service in services:
            futures.append(executor.submit(collect_resource_arns, service, region, all_arns))
        
        # Wait for all tasks to complete
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error in thread: {e}")
    
    # Count total resources found
    total_resources = sum(len(resources) for resources in all_arns.values())
    print(f"Found {total_resources} resources across {len(all_arns)} services")
    
    # Output results
    print("\nAWS Resource ARNs:")
    print("==================")
    
    for service, resources in sorted(all_arns.items()):
        print(f"\n{service.upper()} ({len(resources)} resources):")
        for resource in sorted(resources, key=lambda x: x['arn']):
            # Basic info for all resources
            print(f"  ARN: {resource['arn']}")
            print(f"  Region: {resource['region']}")
            print(f"  Created: {resource['creation_date']}")
            
            # Additional info for specific resource types
            if service == 'ec2':
                print(f"  Private IP: {resource.get('private_ip', 'None')}")
                print(f"  Public IP: {resource.get('public_ip', 'None')}")
            elif service == 's3':
                print(f"  Endpoint: {resource.get('endpoint', 'Unknown')}")
            elif service == 'vpc':
                print(f"  CIDR Block: {resource.get('cidr', 'Unknown')}")
            elif service in ['alb', 'nlb', 'classic_elb']:
                print(f"  Endpoint: {resource.get('endpoint', 'Unknown')}")
                print(f"  Scheme: {resource.get('scheme', 'Unknown')}")
            
            print("  " + "-" * 50)  # Separator between resources
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"aws_resources_{account_id}_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(all_arns, f, indent=2, default=str)
    
    print(f"\nResults saved to {filename}")

if __name__ == "__main__":
    main()