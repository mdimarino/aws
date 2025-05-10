#!/usr/bin/env python3

import boto3

def find_kms_key_usage(kms_key_id):
    # Initialize AWS clients
    s3_client = boto3.client('s3')
    ec2_client = boto3.client('ec2')
    rds_client = boto3.client('rds')
    lambda_client = boto3.client('lambda')
    
    # Find S3 buckets using the KMS key
    def check_s3_buckets():
        buckets = s3_client.list_buckets()['Buckets']
        kms_buckets = []
        for bucket in buckets:
            try:
                enc_conf = s3_client.get_bucket_encryption(Bucket=bucket['Name'])
                rules = enc_conf['ServerSideEncryptionConfiguration']['Rules']
                for rule in rules:
                    if 'KMSMasterKeyID' in rule['ApplyServerSideEncryptionByDefault'] and \
                       rule['ApplyServerSideEncryptionByDefault']['KMSMasterKeyID'] == kms_key_id:
                        kms_buckets.append(bucket['Name'])
            except s3_client.exceptions.ClientError as e:
                if e.response['Error']['Code'] != 'ServerSideEncryptionConfigurationNotFoundError':
                    print(f"Error checking S3 bucket {bucket['Name']}: {e}")
        return kms_buckets
    
    # Find EBS volumes using the KMS key
    def check_ebs_volumes():
        volumes = ec2_client.describe_volumes()['Volumes']
        kms_volumes = [vol['VolumeId'] for vol in volumes if vol.get('KmsKeyId') == kms_key_id]
        return kms_volumes
    
    # Find RDS instances using the KMS key
    def check_rds_instances():
        instances = rds_client.describe_db_instances()['DBInstances']
        kms_instances = [db['DBInstanceIdentifier'] for db in instances if db.get('KmsKeyId') == kms_key_id]
        return kms_instances
    
    # Find Lambda functions using the KMS key
    def check_lambda_functions():
        functions = lambda_client.list_functions()['Functions']
        kms_functions = [func['FunctionName'] for func in functions if func.get('KMSKeyArn') == kms_key_id]
        return kms_functions
    
    # Collect results
    s3_buckets = check_s3_buckets()
    ebs_volumes = check_ebs_volumes()
    rds_instances = check_rds_instances()
    lambda_functions = check_lambda_functions()
    
    # Display results
    print("S3 Buckets using the KMS key:")
    for bucket in s3_buckets:
        print(f" - {bucket}")
    
    print("\nEBS Volumes using the KMS key:")
    for volume in ebs_volumes:
        print(f" - {volume}")
    
    print("\nRDS Instances using the KMS key:")
    for instance in rds_instances:
        print(f" - {instance}")
    
    print("\nLambda Functions using the KMS key:")
    for function in lambda_functions:
        print(f" - {function}")

# Example usage:
kms_key_id = '0b71f056-9b23-4295-8b1a-5011da693d47'
find_kms_key_usage(kms_key_id)

