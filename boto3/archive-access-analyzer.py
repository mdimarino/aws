#!/usr/bin/env python

import boto3

def archive_external_findings(analyzer_name):
    client = boto3.client('accessanalyzer')
    
    # List all active findings
    response = client.list_findings_v2(
        analyzerArn="arn:aws:access-analyzer:sa-east-1:786154173690:analyzer/ConsoleAnalyzer-13102a08-d04d-4eb0-9969-a300e3bd55db",
        filter={
            # 'isExterna': {'eq': ['true']},  # Filters for external access
            'status': {'eq': ['ACTIVE']}   # Only active findings
        }
    )
    
    finding_ids = [finding['id'] for finding in response.get('findings', [])]
    
    # Archive findings
    for finding_id in finding_ids:
        client.update_findings(
            analyzerArn="arn:aws:access-analyzer:sa-east-1:786154173690:analyzer/ConsoleAnalyzer-13102a08-d04d-4eb0-9969-a300e3bd55db",
            findingIds=[finding_id],
            status='ARCHIVED'
        )
        print(f"Archived finding: {finding_id}")

if __name__ == "__main__":
    analyzer_name = "ConsoleAnalyzer-13102a08-d04d-4eb0-9969-a300e3bd55db"  # Change this to your Access Analyzer name
    archive_external_findings(analyzer_name)
