#!/usr/bin/env python3

import boto3
import time

# Initialize the Athena client
client = boto3.client('athena')

# Function to execute a query
def execute_athena_query(query, database, output_location):
    response = client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': database
        },
        ResultConfiguration={
            'OutputLocation': output_location
        }
    )
    return response['QueryExecutionId']

# Function to check the query status
def check_query_status(query_execution_id):
    while True:
        response = client.get_query_execution(QueryExecutionId=query_execution_id)
        status = response['QueryExecution']['Status']['State']
        
        if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            return status
        else:
            time.sleep(5)

# Function to get query results
def get_query_results(query_execution_id):
    response = client.get_query_results(QueryExecutionId=query_execution_id)
    return response

# Main function
def main():
    query = "select * from vpc_flow_logs_seller_prod limit 100;"
    database = "flow_logs"
    output_location = "s3://637423629877-flow-logs/athena_output/"

    query_execution_id = execute_athena_query(query, database, output_location)
    print(f"Query Execution ID: {query_execution_id}")

    status = check_query_status(query_execution_id)
    if status == 'SUCCEEDED':
        print("Query succeeded!")
        results = get_query_results(query_execution_id)
        for row in results['ResultSet']['Rows']:
            print(row)
    else:
        print(f"Query failed with status: {status}")

if __name__ == "__main__":
    main()
