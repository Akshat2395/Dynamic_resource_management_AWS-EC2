"""
CONTAINS ALL THE FUNCTIONS AND CREDENTIALS REQUIRED THROUGHOUT THE APP
"""

import boto3
from botocore.credentials import InstanceMetadataProvider, InstanceMetadataFetcher
import time

# Manager database credentials
db_config = {
    'user': 'manager_database_username',
    'password': 'password',
    'host': 'manager_RDS_ID',
    'database': 'manager database schema name'
}
# User database credentials
db_config2 = {
    'user': 'user_database_username',
    'password': 'password',
    'host': 'user RDS_ID',
    'database': 'user database schema name'
}
# Credentials for EC2/S3/cloudwatch/ELB
provider = InstanceMetadataProvider(iam_role_fetcher=InstanceMetadataFetcher(timeout=1000, num_attempts=2))
creds = provider.load()

AWS_KEY_ID = creds.access_key
AWS_SECRET = creds.secret_key
AWS_SESSION = creds.token

ec2 = boto3.resource('ec2', region_name='us-east-1', aws_access_key_id=AWS_KEY_ID,
                         aws_secret_access_key=AWS_SECRET, aws_session_token=AWS_SESSION)

stats = boto3.client('cloudwatch', region_name='us-east-1', aws_access_key_id=AWS_KEY_ID,
                       aws_secret_access_key=AWS_SECRET, aws_session_token=AWS_SESSION)

s3 = boto3.resource('s3', region_name='us-east-1', aws_access_key_id=AWS_KEY_ID,
                         aws_secret_access_key=AWS_SECRET, aws_session_token=AWS_SESSION)

elb = boto3.client('elb', region_name='us-east-1', aws_access_key_id=AWS_KEY_ID,
                       aws_secret_access_key=AWS_SECRET, aws_session_token=AWS_SESSION)

# Details for creating a new instance
AMI_ID = 'user instance AMI ID'
KEY_NAME = 'private key name'
SEC_GRP = 'launch-wizard-2'
SEC_GRP_ID = 'sg-0e51e46b0edec43fb'
INST_TYPE = 't2.medium'
ELB_NAME = 'A2loadbalancer'
SUBNET_ID = 'subnet-78b44f49'

userdata = '''#!bin/bash
/home/ubuntu/Desktop/start.sh
'''


# Function to unregister the instance from the load balancer.
def dereg_inst_elb(ids):
    response = elb.deregister_instances_from_load_balancer(
        LoadBalancerName=ELB_NAME, Instances=ids,
    )

    waiter = elb.get_waiter('instance_deregistered')
    waiter.wait(LoadBalancerName=ELB_NAME, Instances=ids)
    print(response)


# Function to terminate instances
def term_inst(num_worker):
    instance = ec2.instances.filter(Filters=[{'Name': 'image-id', 'Values': [AMI_ID]},
                                              {'Name': 'instance-state-name', 'Values': ['running']}])
    ids = []
    ids2 = []
    for idx, inst in enumerate(instance, 1):
        ids.append(inst.id)
        ids2.append({'InstanceId': inst.id})
        if idx == num_worker:
            break

    dereg_inst_elb(ids2)
    ec2.instances.filter(InstanceIds=ids).terminate()

    return


# Function to register an instance to the load balancer
def reg_inst_elb(ids):
    response = elb.register_instances_with_load_balancer(
        LoadBalancerName=ELB_NAME, Instances=ids,
    )
    time.sleep(5)
    # waiter = elb.get_waiter('instance_in_service')
    # waiter.wait(LoadBalancerName=ELB_NAME, Instances=ids)

    print(response)


# Function to create an instance
def add_inst(num_worker):
    ec2.create_instances(
        ImageId=AMI_ID,
        MinCount=1,
        MaxCount=num_worker,
        KeyName=KEY_NAME,
        # SecurityGroups=[SEC_GRP],
        IamInstanceProfile={'Name': 'IAM role name'},
        SecurityGroupIds=[SEC_GRP_ID],
        SubnetId=SUBNET_ID,
        UserData=userdata,
        InstanceType=INST_TYPE,
        Monitoring={'Enabled': True}
    )

    instances = ec2.instances.filter(Filters=[{'Name': 'image-id', 'Values': [AMI_ID]},
                                              {'Name': 'instance-state-name', 'Values': ['running', 'pending']}])

    ids = []
    for inst in instances:
        ids.append({'InstanceId': inst.id})

    reg_inst_elb(ids)
    return
