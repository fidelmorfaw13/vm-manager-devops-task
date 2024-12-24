import boto3
from botocore.exceptions import ClientError
import configparser
import json
import os

def get_secret():
    secret_name = "vm-manager-devops-task-secret"  
    region_name = "us-east-2"  
    
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_DEFAULT_REGION')  

    if not aws_access_key_id or not aws_secret_access_key:
        print("Error: AWS credentials not set.")
        raise ValueError("AWS credentials are not available in the environment.")

    
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

    # The secret string is assumed to be in JSON format
    secret = get_secret_value_response['SecretString']

    try:
        secret_dict = json.loads(secret)
    except json.JSONDecodeError as e:
        print(f"Error decoding secret JSON: {e}")
        raise e

   
    print(f"Region from secret: {secret_dict.get('region', aws_region)}")

   
    config = configparser.ConfigParser()

   
    if not config.has_section('default'):
        config.add_section('default')

   
    aws_access_key_id = secret_dict.get('aws_access_key_id', aws_access_key_id)
    aws_secret_access_key = secret_dict.get('aws_secret_access_key', aws_secret_access_key)
    aws_region = secret_dict.get('region', aws_region)  # Fetch the region from the secret

    
    config['default'] = {
        'aws_access_key_id': aws_access_key_id,
        'aws_secret_access_key': aws_secret_access_key,
        'region': aws_region  # This should now have the correct region from the secret
    }

    
    with open('aws_credentials.ini', 'w') as configfile:
        config.write(configfile)

if __name__ == "__main__":
    get_secret()
