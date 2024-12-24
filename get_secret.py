import boto3
from botocore.exceptions import ClientError
import configparser
import json

def get_secret():
    secret_name = "vm-manager-devops-task-secret"  # Replace with your actual secret name
    region_name = "us-east-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
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
        'region': 'us-east-2'  # Set region explicitly or fetch it from secret if needed
    }

    with open('aws_credentials.ini', 'w') as configfile:
        config.write(configfile)

if __name__ == "__main__":
    get_secret()
