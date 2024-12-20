from flask import Flask, request, jsonify
from flask_cors import CORS  # Import flask-cors
import boto3
import configparser
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Load AWS credentials from custom file
config = configparser.ConfigParser()
config.read('aws_credentials.ini')

aws_access_key = config['default']['aws_access_key_id']
aws_secret_key = config['default']['aws_secret_access_key']
region = config['default']['region']

# AWS EC2 client using credentials from the file
try:
    ec2_client = boto3.client('ec2',
                              aws_access_key_id=aws_access_key,
                              aws_secret_access_key=aws_secret_key,
                              region_name=region)
    print("EC2 client initialized successfully.")
except Exception as e:
    print(f"Error initializing EC2 client: {e}")
    ec2_client = None

# Sample in-memory user storage
users = {
    'user1': {'password': generate_password_hash('password1'), 'instances': []},
    'user2': {'password': generate_password_hash('password2'), 'instances': []},
}

# Helper function to create EC2 instance
def create_instance(username, instance_type, os_type):
    if not ec2_client:
        return None  # If EC2 client is not initialized, return None
    
    try:
        ami_id = 'ami-0c55b159cbfafe1f0' if os_type == 'linux' else 'ami-0d5d9d301c853a04a'  # Modify for your region
        print(f"Creating instance for user: {username}, OS: {os_type}, Type: {instance_type}")
        
        instance = ec2_client.run_instances(
            ImageId=ami_id,
            InstanceType=instance_type,
            MinCount=1,
            MaxCount=1
        )
        
        instance_id = instance['Instances'][0]['InstanceId']
        print(f"Instance created with ID: {instance_id}")
        
        users[username]['instances'].append(instance_id)
        return instance_id
    except Exception as e:
        print(f"Error creating instance for {username}: {e}")
        return None

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
    print(f"Received username: {username}, password: {password}")
    user = users.get(username)
    if not user or not check_password_hash(user['password'], password):
        print("Authentication failed.")
        return jsonify({'error': 'Unauthorized'}), 403
    
    instance_type = data.get('instance_type')
    os_type = data.get('os_type')
    
    instance_id = create_instance(username, instance_type, os_type)
    
    if instance_id:
        return jsonify({'instance_id': instance_id})
    else:
        return jsonify({'error': 'Failed to create instance'}), 500

@app.route('/instances', methods=['GET'])
def get_instances():
    username = request.headers.get('username')
    password = request.headers.get('password')
    
    print(f"Fetching instances for user: {username}")
    
    user = users.get(username)
    if not user or not check_password_hash(user['password'], password):
        print("Authentication failed.")
        return jsonify({'error': 'Unauthorized'}), 403
    
    if not user['instances']:
        print(f"No instances found for {username}.")
        return jsonify({'error': 'No instances found'}), 404
    
    print(f"Instances for {username}: {user['instances']}")
    return jsonify({'instances': user['instances']})

@app.route('/delete_instance', methods=['POST'])
def delete_instance():
    data = request.get_json()
    username = request.headers.get('username')
    password = request.headers.get('password')
    
    # Validate user
    print(f"Received username: {username}, password: {password}")
    user = users.get(username)
    if not user or not check_password_hash(user['password'], password):
        print("Authentication failed.")
        return jsonify({'error': 'Unauthorized'}), 403

    instance_id = data.get('instance_id')
    
    if instance_id not in user['instances']:
        return jsonify({'error': 'Cannot delete instance created by another user'}), 403

    # Terminate EC2 instance
    try:
        ec2_client.terminate_instances(InstanceIds=[instance_id])
        print(f"Terminated instance with ID: {instance_id}")
    except Exception as e:
        print(f"Error terminating instance: {e}")
        return jsonify({'error': 'Failed to delete instance'}), 500
    
    user['instances'].remove(instance_id)
    
    return jsonify({'message': 'Instance deleted successfully'})

if __name__ == '__main__':
    app.run(debug=True)
