import boto3
from botocore.exceptions import ClientError
import configparser
import json
import os

def get_secret():
    secret_name = "vm-manager-devops-task-secret"  
    
    
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    if not aws_access_key_id or not aws_secret_access_key:
        print("Error: AWS credentials not set.")
        raise ValueError("AWS credentials are not available in the environment.")

    
    session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )

    # Create a Secrets Manager client using the session
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

    aws_access_key_id = secret_dict.get('aws_access_key_id', '')
    aws_secret_access_key = secret_dict.get('aws_secret_access_key', '')
    aws_region = secret_dict.get('region', '')  

    if not aws_region:
        print("Error: Region not found in the secret.")
        raise ValueError("Region is not set in the secret.")

    # Debugging: print out the region fetched from the secret
    print(f"Region from secret: {aws_region}")

    
    config = configparser.ConfigParser()

    # Ensure we have a 'default' section in the INI file
    if not config.has_section('default'):
        config.add_section('default')

   
    config['default'] = {
        'aws_access_key_id': aws_access_key_id,
        'aws_secret_access_key': aws_secret_access_key,
        'region': aws_region 
    }


    with open('aws_credentials.ini', 'w') as configfile:
        config.write(configfile)

if __name__ == "__main__":
    get_secret()
