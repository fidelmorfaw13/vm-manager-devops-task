from flask import Flask, request, jsonify
from flask_cors import CORS  # Import flask-cors
import boto3
import json
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Retrieve AWS credentials from Secrets Manager
def get_aws_credentials(secret_name, region_name='us-east-1'):
    secrets_client = boto3.client('secretsmanager', region_name=region_name)
    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])
        return secret['aws_access_key_id'], secret['aws_secret_access_key'], secret['region']
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve AWS credentials: {e}")

# Fetch credentials from Secrets Manager
SECRET_NAME = 'my-app-aws-credentials'  # Replace with your secret name
aws_access_key, aws_secret_key, region = get_aws_credentials(SECRET_NAME)

# AWS EC2 client using credentials from Secrets Manager
ec2_client = boto3.client('ec2',
                          aws_access_key_id=aws_access_key,
                          aws_secret_access_key=aws_secret_key,
                          region_name=region)

# Sample in-memory user storage
users = {
    'user1': {'password': generate_password_hash('password1'), 'instances': []},
    'user2': {'password': generate_password_hash('password2'), 'instances': []},
}

# Helper function to create EC2 instance
def create_instance(username, instance_type, os_type):
    ami_id = 'ami-0c55b159cbfafe1f0' if os_type == 'linux' else 'ami-0d5d9d301c853a04a'  # Modify for your region
    instance = ec2_client.run_instances(
        ImageId=ami_id,
        InstanceType=instance_type,
        MinCount=1,
        MaxCount=1
    )
    instance_id = instance['Instances'][0]['InstanceId']
    users[username]['instances'].append(instance_id)
    return instance_id

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
   
    user = users.get(username)
    if user and check_password_hash(user['password'], password):
        return jsonify({'message': 'Login successful'})
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/create_instance', methods=['POST'])
def create_instance_route():
    data = request.get_json()
    username = request.headers.get('username')
    password = request.headers.get('password')
   
    # Validate user
    user = users.get(username)
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'error': 'Unauthorized'}), 403
   
    instance_type = data.get('instance_type')
    os_type = data.get('os_type')
   
    instance_id = create_instance(username, instance_type, os_type)
    return jsonify({'instance_id': instance_id})

@app.route('/instances', methods=['GET'])
def get_instances():
    username = request.headers.get('username')
    password = request.headers.get('password')
   
    user = users.get(username)
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'error': 'Unauthorized'}), 403
   
    return jsonify({'instances': user['instances']})

@app.route('/delete_instance', methods=['POST'])
def delete_instance():
    data = request.get_json()
    username = request.headers.get('username')
    password = request.headers.get('password')
   
    # Validate user
    user = users.get(username)
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'error': 'Unauthorized'}), 403

    instance_id = data.get('instance_id')
   
    if instance_id not in user['instances']:
        return jsonify({'error': 'processing'}), 403

    # Terminate EC2 instance
    ec2_client.terminate_instances(InstanceIds=[instance_id])
    user['instances'].remove(instance_id)
   
    return jsonify({'message': 'Instance deleted successfully'})

if __name__ == '__main__':
    app.run(debug=True)
