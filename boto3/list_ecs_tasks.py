import boto3

def list_ecs_tasks():
    # Create a session using your AWS credentials
    session = boto3.Session(aws_access_key_id='YOUR_ACCESS_KEY', aws_secret_access_key='YOUR_SECRET_KEY')
    
    # Initialize the ECS client with the above session
    ecs = session.client('ecs')

    # Get a list of all clusters in your AWS account
    response = ecs.list_clusters()
    cluster_arns = response['clusterArns']

    for cluster_arn in cluster_arns:
        # Get details about each task within the current cluster
        tasks = ecs.list_tasks(cluster=cluster_arn)

        if 'taskArns' not in tasks:
            continue

        for task_arn in tasks['taskArns']:
            description = ecs.describe_tasks(cluster=cluster_arn, tasks=[task_arn])

            # Check that the task does not have a specific tag ("Billing")
            if 'tags' in description and 'Billing' in description['tags']:
                continue

            print("Task ARN: {}".format(description['tasks'][0]['taskArn']))


if __name__ == "" == "main" :
    list_ecs_tasks()
