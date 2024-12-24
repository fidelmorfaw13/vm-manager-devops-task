import boto3
from botocore.exceptions import ClientError
import configparser
import json
import os

def get_secret():
    secret_name = "vm-manager-devops-task-secret"  
    region_name = "us-east-2"  

    # Get AWS credentials from environment variables (set by GitHub Actions)
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_DEFAULT_REGION', region_name) 

    if not aws_access_key_id or not aws_secret_access_key:
        print("Error: AWS credentials not set.")
        raise ValueError("AWS credentials are not available in the environment.")

    # Create a session using the AWS credentials
    session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region
    )

    
    client = session.client(service_name='secretsmanager')

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        print(f"Error fetching secret: {e}")
        raise e

    
    secret = get_secret_value_response['SecretString']

    try:
        secret_dict = json.loads(secret)
    except json.JSONDecodeError as e:
        print(f"Error decoding secret JSON: {e}")
        raise e

    # Now let's write these values into aws_credentials.ini
    config = configparser.ConfigParser()
    
    # Ensure we have a 'default' section in the INI file
    if not config.has_section('default'):
        config.add_section('default')

    
    aws_access_key_id = secret_dict.get('aws_access_key_id', aws_access_key_id)
    aws_secret_access_key = secret_dict.get('aws_secret_access_key', aws_secret_access_key)
    aws_region = secret_dict.get('region', aws_region)  # If region exists in secret, use it

   
    config['default'] = {
        'aws_access_key_id': aws_access_key_id,
        'aws_secret_access_key': aws_secret_access_key,
        'region': aws_region  
    }

    
    with open('aws_credentials.ini', 'w') as configfile:
        config.write(configfile)

if __name__ == "__main__":
    get_secret()
