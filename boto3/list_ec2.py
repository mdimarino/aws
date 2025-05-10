#!/usr/bin/env python3

import boto3
import csv

# Initialize a session using Amazon EC2
session = boto3.Session()
ec2_client = session.client('ec2')

# Retrieve a list of EC2 instances
response = ec2_client.describe_instances()

# Function to calculate total volume size for an instance
def get_total_volume_size(instance_id):
    total_size = 0
    volumes = ec2_client.describe_volumes(Filters=[{'Name': 'attachment.instance-id', 'Values': [instance_id]}])
    for volume in volumes['Volumes']:
        total_size += volume['Size']
    return total_size

# Open a CSV file to write the output
with open('ec2_instances.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Name', 'Instance ID', 'Instance State', 'Total Volume Size (GB)'])

    # Loop through each instance and extract the required information
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            instance_state = instance['State']['Name']
            total_volume_size = get_total_volume_size(instance_id)
            name = None
            # Extract the Name tag if it exists
            if 'Tags' in instance:
                for tag in instance['Tags']:
                    if tag['Key'] == 'Name':
                        name = tag['Value']
                        break

            writer.writerow([name, instance_id, instance_state, total_volume_size])

print("EC2 instances have been written to ec2_instances.csv")
