#!/usr/bin/env python

""" verifica se os ALBs criados na AWS têm entradas no Route53 de uma hosted zone"""

import boto3


def list_alb_dns_names():
    """ list_alb_dns_names """

    elbv2_client = boto3.client('elbv2')

    response = elbv2_client.describe_load_balancers()

    return [lb['DNSName'] for lb in response['LoadBalancers']]


def processa_entradas(response, alb_dns_name):
    """ processa_entradas """
    for record_set in response['ResourceRecordSets']:
        if 'AliasTarget' in record_set and 'DNSName' in record_set['AliasTarget']:
            if alb_dns_name in record_set['AliasTarget']['DNSName']:
                print(f"{record_set['Name']} {alb_dns_name}")


def check_alb_in_route53(hosted_zone_id, alb_dns_name):
    """ check_alb_in_route53 """
    client = boto3.client('route53')

    response = client.list_resource_record_sets(HostedZoneId=hosted_zone_id)

    processa_entradas(response, alb_dns_name)

    while 'NextRecordName' in response:
        response = client.list_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            StartRecordName=response['NextRecordName'],
            StartRecordType=response['NextRecordType']
        )

        processa_entradas(response, alb_dns_name)


if __name__ == "__main__":

    HOSTED_ZONE_ID = "Z22PGG9II0I7L0"

    for alb_dns_names in list_alb_dns_names():
        check_alb_in_route53(HOSTED_ZONE_ID, alb_dns_names)
