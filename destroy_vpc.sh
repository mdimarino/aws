#!/bin/bash

echo =================================================================================

    aws --profile ${profile} ec2 delete-vpc \
        --vpc-id ${vpc_id}

echo; echo =================================================================================

    aws --profile ${profile} ec2 delete-dhcp-options \
        --dhcp-options-id ${dhcp_options_id}

echo; echo =================================================================================

    aws --profile ${profile} route53 delete-hosted-zone \
        --id ${hosted_zone_id} \
        --output text

echo; echo =================================================================================
