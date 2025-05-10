#!/usr/bin/env python

""" lista elementos ECS sem tag Billing """

import boto3

def get_ecs_tasks_without_billing_tag():
    ecs_client = boto3.client('ecs')

    # List all ECS clusters
    clusters = ecs_client.list_clusters()['clusterArns']

    for cluster in clusters:
        # List tasks for each cluster
        tasks = ecs_client.list_tasks(cluster=cluster)['taskArns']

        for task in tasks:
            # Describe task to get details
            task_details = ecs_client.describe_tasks(
                cluster=cluster,
                tasks=[task]
            )['tasks'][0]

            # Check if Billing tag is present
            billing_tag_found = False
            for tag in task_details.get('tags', []):
                if tag['key'] == 'Billing':
                    billing_tag_found = True
                    break

            # Print task details if Billing tag is not found
            if not billing_tag_found:
                print(f"Cluster: {cluster}, Task ARN: {task_details['taskArn']}")


if __name__ == "__main__":
    get_ecs_tasks_without_billing_tag()
