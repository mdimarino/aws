#!/usr/bin/env python

""" lista elementos ECS sem tag Billing """

import boto3


def list_acm_domains_with_email_validation():
    # Create a boto3 ACM client
    acm_client = boto3.client('acm', region_name='us-east-1')

    # List all certificates
    response = acm_client.list_certificates()

    # Extract domain names with email validation from the response
    domains_with_email_validation = []
    for cert in response['CertificateSummaryList']:
        cert_details = acm_client.describe_certificate(CertificateArn=cert['CertificateArn'])
        if cert_details['Certificate']['DomainValidationOptions']:
            for validation_option in cert_details['Certificate']['DomainValidationOptions']:
                if validation_option['ValidationMethod'] == 'EMAIL':
                    domains_with_email_validation.append(cert['DomainName'])

    return domains_with_email_validation


def main():
    # List ACM domains with email validation
    domains_with_email_validation = list_acm_domains_with_email_validation()

    # Print the list of domains using email validation
    print("Domains using email validation for domain ownership verification:")
    for domain in domains_with_email_validation:
        print(domain)


if __name__ == "__main__":
    main()
