import boto3
from botocore.exceptions import ClientError
import configparser
import json
import os

def get_secret():
    secret_name = "vm-manager-devops-task-secret"  # Replace with your actual secret name
    region_name = "us-east-2"

    # Get AWS credentials from environment variables (set by GitHub Actions)
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_DEFAULT_REGION', region_name)  # Default to us-east-2 if not set

    if not aws_access_key_id or not aws_secret_access_key:
        print("Error: AWS credentials not set.")
        raise ValueError("AWS credentials are not available in the environment.")

    # Create a session using the AWS credentials
    session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region
    )
    
    # Create a Secrets Manager client using the session
    client = session.client(service_name='secretsmanager')

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        print(f"Error fetching secret: {e}")
        raise e

    secret = get_secret_value_response['SecretString']

    # Assuming the secret is in JSON format
    secret_dict = json.loads(secret)

    # Now let's write these values into aws_credentials.ini
    config = configparser.ConfigParser()
    config.read('aws_credentials.ini')

    # Save the secret values to the INI file under the default profile
    config['default'] = {
        'aws_access_key_id': secret_dict.get('aws_access_key_id', ''),
        'aws_secret_access_key': secret_dict.get('aws_secret_access_key', ''),
        'region': aws_region  # Set region explicitly or fetch it from secret if needed
    }

    with open('aws_credentials.ini', 'w') as configfile:
        config.write(configfile)

if __name__ == "__main__":
    get_secret()
