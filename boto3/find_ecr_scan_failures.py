#!/usr/bin/env python

""" lista repositórios ECR com falhas no scan de imagens """

import boto3

def get_latest_image_digest(repository_name, region_name='us-east-1'):
    """
    Retrieves the image digest of the latest image in the specified ECR repository.

    Args:
    - repository_name: Name of the ECR repository.
    - region_name: AWS region where the ECR repository is located. Default is 'us-east-1'.

    Returns:
    - Image digest of the latest image in the repository.
    """
    ecr_client = boto3.client('ecr', region_name=region_name)

    response = ecr_client.describe_images(repositoryName=repository_name)
    images = response['imageDetails']
    if images:
        latest_image = max(images, key=lambda x: x['imagePushedAt'])
        return latest_image['imageDigest']
    else:
        return None


def get_failed_scan_findings_all_repositories(region_name='us-east-1'):
    """
    Retrieves failed image scan findings for all ECR repositories in the specified AWS region.

    Args:
    - region_name: AWS region where the ECR repositories are located. Default is 'us-east-1'.

    Returns:
    - Dictionary where keys are repository names and values are lists of failed image scan findings.
    """
    ecr_client = boto3.client('ecr', region_name=region_name)

    response = ecr_client.describe_repositories()
    repositories = response['repositories']

    failed_findings_all_repositories = {}

    for repository in repositories:
        repository_name = repository['repositoryName']
        
        latest_image_digest = get_latest_image_digest(repository_name, region_name)
        if latest_image_digest:
            response = ecr_client.describe_image_scan_findings(
                repositoryName=repository_name,
                imageId={'imageDigest': latest_image_digest}
            )

            failed_findings = []
            if 'imageScanFindings' in response and 'findings' in response['imageScanFindings']:
                findings = response['imageScanFindings']['findings']
                for finding in findings:
                    if finding['severity'] == 'CRITICAL' or finding['severity'] == 'HIGH':
                        failed_findings.append(finding)

            failed_findings_all_repositories[repository_name] = failed_findings
        else:
            failed_findings_all_repositories[repository_name] = []

    return failed_findings_all_repositories

# Example usage:
region_name = 'us-east-1'
failed_findings_all_repositories = get_failed_scan_findings_all_repositories(region_name)

for repository_name, failed_findings in failed_findings_all_repositories.items():
    if failed_findings:
        print(f"Repository: {repository_name}")
        print("Failed Image Scan Findings:")
        for finding in failed_findings:
            print(f"Severity: {finding['severity']}, Description: {finding['description']}")
    else:
        print(f"No failed image scan findings found for repository: {repository_name}")
