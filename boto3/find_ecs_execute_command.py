#!/usr/bin/env python

"""
AWS IAM Scanner for ecs:ExecuteCommand permission

This script scans your AWS environment to find IAM roles, groups, and users
that have inline policies with the "ecs:ExecuteCommand" permission. It also 
identifies customer-managed policies that include this permission. AWS Managed
policies are excluded from the search.

Requirements:
- boto3
- AWS credentials configured

Usage:
python iam_ecs_execute_command_scanner.py
"""

import json
import re
from botocore.exceptions import ClientError
import boto3


def check_policy_for_ecs_execute_command(policy_doc):
    """
    Check if a policy document contains ecs:ExecuteCommand permission
    Returns True if found, False otherwise
    """
    if isinstance(policy_doc, str):
        try:
            policy_doc = json.loads(policy_doc)
        except json.JSONDecodeError:
            print("Error: Invalid policy document format")
            return False

    # Function to recursively search through policy document
    def search_policy(obj):
        if isinstance(obj, dict):
            # Check for Action or actions in policy
            for key in ['Action', 'action', 'Actions', 'actions']:
                if key in obj:
                    actions = obj[key]
                    if isinstance(actions, str):
                        actions = [actions]
                    for action in actions:
                        # Check for exact match or wildcard patterns that would
                        # include ecs:ExecuteCommand
                        if action == "ecs:ExecuteCommand" or \
                           action == "ecs:*" or action == "*":
                            return True
                        # Check for wildcards like ecs:Execute*
                        if '*' in action and action.startswith('ecs:'):
                            pattern = action.replace('*', '.*')
                            if re.match(pattern, 'ecs:ExecuteCommand'):
                                return True

            # Recursively check all values in the dictionary
            for value in obj.values():
                if search_policy(value):
                    return True

        elif isinstance(obj, list):
            # Recursively check all items in the list
            for item in obj:
                if search_policy(item):
                    return True

        return False

    # Start the search from the Statement part of the policy
    if 'Statement' in policy_doc:
        return search_policy(policy_doc['Statement'])

    return False


def scan_iam_for_ecs_execute_command():
    """
    Scan IAM for roles, groups, and users that have inline policies with
    ecs:ExecuteCommand
    Also scan customer managed policies for ecs:ExecuteCommand
    Excludes AWS Managed policies
    """
    iam_client = boto3.client('iam')

    results = {
        'roles': [],
        'groups': [],
        'users': [],
        'managed_policies': []
    }

    # First scan customer managed policies to build a reference list
    print("\nScanning Customer Managed Policies...")
    paginator = iam_client.get_paginator('list_policies')

    # Only check customer managed policies (Scope='Local')
    for page in paginator.paginate(Scope='Local'):
        for policy in page['Policies']:
            policy_arn = policy['Arn']
            policy_name = policy['PolicyName']

            try:
                policy_version = iam_client.get_policy_version(
                    PolicyArn=policy_arn,
                    VersionId=policy['DefaultVersionId']
                )
                if check_policy_for_ecs_execute_command(
                   policy_version['PolicyVersion']['Document']
                   ):
                    results['managed_policies'].append({
                        'name': policy_name,
                        'arn': policy_arn,
                        'type': 'Customer managed'
                    })
                    print(f"  Found: Customer managed policy '{policy_name}' ({policy_arn})")
            except ClientError as e:
                print(f"  Error getting policy version for {policy_name}: {e}")

    # Scan roles
    print("\nScanning IAM Roles...")
    paginator = iam_client.get_paginator('list_roles')
    for page in paginator.paginate():
        for role in page['Roles']:
            role_name = role['RoleName']

            # Check inline policies
            try:
                policy_paginator = iam_client.get_paginator('list_role_policies')
                for policy_page in policy_paginator.paginate(RoleName=role_name):
                    for policy_name in policy_page['PolicyNames']:
                        policy_response = iam_client.get_role_policy(
                            RoleName=role_name,
                            PolicyName=policy_name
                        )
                        if check_policy_for_ecs_execute_command(policy_response['PolicyDocument']):
                            results['roles'].append({
                                'name': role_name,
                                'policy_type': 'inline',
                                'policy_name': policy_name
                            })
                            print(f"  Found: Role '{role_name}' with inline policy '{policy_name}'")
            except ClientError as e:
                print(f"  Error getting policies for role {role_name}: {e}")

            # Check attached customer managed policies (AWS managed policies are excluded)
            try:
                attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)
                for policy in attached_policies['AttachedPolicies']:
                    policy_arn = policy['PolicyArn']
                    # Only consider customer managed policies (not starting with 'arn:aws:iam::aws:')
                    if not policy_arn.startswith('arn:aws:iam::aws:') and any(p['arn'] == policy_arn for p in results['managed_policies']):
                        results['roles'].append({
                            'name': role_name,
                            'policy_type': 'managed',
                            'policy_name': policy['PolicyName'],
                            'policy_arn': policy_arn
                        })
                        print(f"  Found: Role '{role_name}' with attached customer managed policy '{policy['PolicyName']}'")
            except ClientError as e:
                print(f"  Error getting attached policies for role {role_name}: {e}")

    # Scan groups
    print("\nScanning IAM Groups...")
    paginator = iam_client.get_paginator('list_groups')
    for page in paginator.paginate():
        for group in page['Groups']:
            group_name = group['GroupName']

            # Check inline policies
            try:
                policy_paginator = iam_client.get_paginator('list_group_policies')
                for policy_page in policy_paginator.paginate(GroupName=group_name):
                    for policy_name in policy_page['PolicyNames']:
                        policy_response = iam_client.get_group_policy(
                            GroupName=group_name,
                            PolicyName=policy_name
                        )
                        if check_policy_for_ecs_execute_command(policy_response['PolicyDocument']):
                            results['groups'].append({
                                'name': group_name,
                                'policy_type': 'inline',
                                'policy_name': policy_name
                            })
                            print(f"  Found: Group '{group_name}' with inline policy '{policy_name}'")
            except ClientError as e:
                print(f"  Error getting policies for group {group_name}: {e}")

            # Check attached customer managed policies (AWS managed policies are excluded)
            try:
                attached_policies = iam_client.list_attached_group_policies(GroupName=group_name)
                for policy in attached_policies['AttachedPolicies']:
                    policy_arn = policy['PolicyArn']
                    # Only consider customer managed policies (not starting with 'arn:aws:iam::aws:')
                    if not policy_arn.startswith('arn:aws:iam::aws:') and any(p['arn'] == policy_arn for p in results['managed_policies']):
                        results['groups'].append({
                            'name': group_name,
                            'policy_type': 'managed',
                            'policy_name': policy['PolicyName'],
                            'policy_arn': policy_arn
                        })
                        print(f"  Found: Group '{group_name}' with attached customer managed policy '{policy['PolicyName']}'")
            except ClientError as e:
                print(f"  Error getting attached policies for group {group_name}: {e}")

    # Scan users
    print("\nScanning IAM Users...")
    paginator = iam_client.get_paginator('list_users')
    for page in paginator.paginate():
        for user in page['Users']:
            user_name = user['UserName']

            # Check inline policies
            try:
                policy_paginator = iam_client.get_paginator('list_user_policies')
                for policy_page in policy_paginator.paginate(UserName=user_name):
                    for policy_name in policy_page['PolicyNames']:
                        policy_response = iam_client.get_user_policy(
                            UserName=user_name,
                            PolicyName=policy_name
                        )
                        if check_policy_for_ecs_execute_command(policy_response['PolicyDocument']):
                            results['users'].append({
                                'name': user_name,
                                'policy_type': 'inline',
                                'policy_name': policy_name
                            })
                            print(f"  Found: User '{user_name}' with inline policy '{policy_name}'")
            except ClientError as e:
                print(f"  Error getting policies for user {user_name}: {e}")

            # Check attached customer managed policies (AWS managed policies are excluded)
            try:
                attached_policies = iam_client.list_attached_user_policies(UserName=user_name)
                for policy in attached_policies['AttachedPolicies']:
                    policy_arn = policy['PolicyArn']
                    # Only consider customer managed policies (not starting with 'arn:aws:iam::aws:')
                    if not policy_arn.startswith('arn:aws:iam::aws:') and any(p['arn'] == policy_arn for p in results['managed_policies']):
                        results['users'].append({
                            'name': user_name,
                            'policy_type': 'managed',
                            'policy_name': policy['PolicyName'],
                            'policy_arn': policy_arn
                        })
                        print(f"  Found: User '{user_name}' with attached customer managed policy '{policy['PolicyName']}'")
            except ClientError as e:
                print(f"  Error getting attached policies for user {user_name}: {e}")

    return results


def print_summary(results):
    """
    Print a summary of the scan results
    """
    print("\n" + "="*80)
    print("SUMMARY: IAM ENTITIES WITH ecs:ExecuteCommand PERMISSION")
    print("="*80)

    print("\nIAM Roles with ecs:ExecuteCommand:")
    if not results['roles']:
        print("  None found")
    else:
        for role in results['roles']:
            if role['policy_type'] == 'inline':
                print(f"  Role: {role['name']} (inline policy: {role['policy_name']})")
            else:
                print(f"  Role: {role['name']} (customer managed policy: {role['policy_name']})")

    print("\nIAM Groups with ecs:ExecuteCommand:")
    if not results['groups']:
        print("  None found")
    else:
        for group in results['groups']:
            if group['policy_type'] == 'inline':
                print(f"  Group: {group['name']} (inline policy: {group['policy_name']})")
            else:
                print(f"  Group: {group['name']} (customer managed policy: {group['policy_name']})")

    print("\nIAM Users with ecs:ExecuteCommand:")
    if not results['users']:
        print("  None found")
    else:
        for user in results['users']:
            if user['policy_type'] == 'inline':
                print(f"  User: {user['name']} (inline policy: {user['policy_name']})")
            else:
                print(f"  User: {user['name']} (customer managed policy: {user['policy_name']})")

    print("\nCustomer Managed Policies with ecs:ExecuteCommand:")
    if not results['managed_policies']:
        print("  None found")
    else:
        for policy in results['managed_policies']:
            print(f"  {policy['name']} ({policy['arn']})")

    print("\n" + "="*80)


def main():
    """ Main Function """
    print("AWS IAM Scanner for ecs:ExecuteCommand Permission")
    print("="*80)
    print("Scanning your AWS environment for IAM entities with ecs:ExecuteCommand permission...")
    print("NOTE: AWS Managed policies are excluded from this scan")

    try:
        results = scan_iam_for_ecs_execute_command()
        print_summary(results)

        # Save results to a JSON file
        with open("ecs_execute_command_scan_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print("\nResults saved to: ecs_execute_command_scan_results.json")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("\nMake sure your AWS credentials are properly configured with the appropriate IAM permissions.")


if __name__ == "__main__":
    main()
