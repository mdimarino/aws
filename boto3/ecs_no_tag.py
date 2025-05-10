#!/usr/bin/env python

""" lista elementos ECS sem tag Billing """

import boto3


def get_ecs_services_without_billing_tag():
    ecs_client = boto3.client('ecs')

    # List all ECS clusters
    clusters = ecs_client.list_clusters()['clusterArns']

    for cluster in clusters:
        # List services for each cluster
        services = ecs_client.list_services(cluster=cluster)['serviceArns']

        for service in services:
            # Describe service to get details
            service_details = ecs_client.describe_services(
                cluster=cluster,
                services=[service]
            )['services'][0]

            # Check if Billing tag is present
            billing_tag_found = False
            for tag in service_details.get('tags', []):
                if tag['key'] == 'Billing':
                    billing_tag_found = True
                    break

            # Print service details if Billing tag is not found
            if not billing_tag_found:
                print(f"Cluster: {cluster}, Service: {service_details['serviceName']}")


if __name__ == "__main__":
    get_ecs_services_without_billing_tag()
