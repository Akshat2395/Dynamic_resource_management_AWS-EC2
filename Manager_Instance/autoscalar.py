"""
STANDALONE PROGRAM WHICH RUNS CONTINUOUSLY AND FUNCTIONS WHEN APP IS SET TO AUTOMATIC MODE
"""
# Test code to simulate user traffic
# python3 gen.py http://A2loadbalancer-1041861342.us-east-1.elb.amazonaws.com/api/upload admin ECE1779pass 1 ./load_images/ 100

import boto3
import time
from botocore.credentials import InstanceMetadataProvider, InstanceMetadataFetcher
from datetime import datetime, timedelta
import mysql.connector


db_config = {
    'user': 'database_username',
    'password': 'password',
    'host': 'RDS_ID',
    'database': 'database_name'
}

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

AMI_ID = 'Instance AMI ID'
KEY_NAME = 'private key name'
SEC_GRP = 'launch-wizard-2'
SEC_GRP_ID = 'security_group_id'
INST_TYPE = 't2.medium'
ELB_NAME = 'A2loadbalancer'
SUBNET_ID = 'subnet-78b44f49'


def connect_to_database():
    return mysql.connector.connect(user=db_config['user'],
                                   password=db_config['password'],
                                   host=db_config['host'],
                                   database=db_config['database'])


# REGISTER INSTANCE TO ELB
def reg_inst_elb(ids):
    response = elb.register_instances_with_load_balancer(
        LoadBalancerName=ELB_NAME, Instances=ids,
    )
    # time.sleep(20)
    waiter = elb.get_waiter('instance_in_service')
    waiter.wait(LoadBalancerName=ELB_NAME, Instances=ids)

    print(response)


# Unregister instance from ELB
def dereg_inst_elb(ids):
    response = elb.deregister_instances_from_load_balancer(
        LoadBalancerName=ELB_NAME, Instances=ids,
    )

    waiter = elb.get_waiter('instance_deregistered')
    waiter.wait(LoadBalancerName=ELB_NAME, Instances=ids)
    print(response)


userdata = '''#!bin/bash
/home/ubuntu/Desktop/start.sh
'''


# CREATE INSTANCES
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


# TERMINATE INSTANCES
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


# Master function to check if app is set to auto mode
# Also calculate if additional instances should be created or terminated based on the average CPU utilization
def auto_man(auto=True, max_thr=80, min_thr=30, add_rate=1.5, del_rate=0.5, num_add=0, num_term=0):
    if auto:
        instances = ec2.instances.filter(Filters=[{'Name': 'image-id', 'Values': [AMI_ID]},
                                              {'Name': 'instance-state-name', 'Values': ['running', 'pending']}])

        ids = []
        cpu_stats = []
        for inst in instances:
            ids.append(inst.id)
            print(inst.id, flush=True)

            # Get CPU metrics in the intervals of 2 minute

            metrics = stats.get_metric_statistics(
                Period=60,
                StartTime=datetime.utcnow() - timedelta(seconds=2*60),
                EndTime=datetime.utcnow() - timedelta(seconds=60),
                MetricName='CPUUtilization',
                Namespace='AWS/EC2',
                Statistics=['Average'],
                Dimensions=[{'Name': 'InstanceId', 'Value': inst.id}]
            )

            for data in metrics['Datapoints']:
                load = round(data['Average'], 2)
                cpu_stats.append(load)

        print("cpu_stats: ", cpu_stats, flush=True)
        num_workers = len(cpu_stats)
        add_inst_num = 0
        red_inst_num = 0

        if num_workers != 0:
            average_load = sum(cpu_stats)/num_workers
        else:
            average_load = 0

        """ ---------------------ADD INSTANCE-------------------- """

        if average_load >= max_thr:
            if add_rate >= 1:
                add_inst_num = round(num_workers * add_rate - num_workers)
                if add_inst_num == 0:
                    add_inst_num = add_rate
                if (add_inst_num + num_workers) > 8:
                    add_inst_num = min(max(0, (8 - num_workers)), (8 - num_workers))
                if add_inst_num > 0:
                    add_inst(int(add_inst_num))
                    print("Auto - Added {} instance".format(add_inst_num), flush=True)

        """ ---------------------TERMINATE INSTANCE-------------------- """

        if average_load <= min_thr:
            if num_workers != 1:
                red_inst_num = round(num_workers - num_workers * del_rate)
                if (num_workers - red_inst_num) < 1:
                    red_inst_num = num_workers - 1
                if red_inst_num > 0:
                    term_inst(int(red_inst_num))
                    print("Auto - Terminated {} instance".format(red_inst_num), flush=True)
        return
    else:
        return

"""
if num_add > 0 and num_term == 0:
    add_inst(num_add)
    print("Manual - Added {} instance".format(num_add), flush=True)
    # err = "Added instance"

    cnx = connect_to_database()
    cursor = cnx.cursor()
    num_add = 0
    query = 'UPDATE autoscalar SET num_add=%s where id = 1'
    cursor.execute(query, (num_add,))
    cnx.commit()
    cnx.close()

    return
elif num_add == 0 and num_term > 0:
    term_inst(num_term)
    print("manual - Terminated {} instance".format(num_term), flush=True)
    # err = "Terminated instance"

    cnx = connect_to_database()
    cursor = cnx.cursor()
    num_term = 0
    query = 'UPDATE autoscalar SET num_term=%s where id = 1'
    cursor.execute(query, (num_term,))
    cnx.commit()
    cnx.close()

    return
else:
    # err = "Error"
    return
"""

# Run this part indefinitely
while True:
    # ON STARTUP - check if any workers are running or not
    instances = ec2.instances.filter(Filters=[{'Name': 'image-id', 'Values': [AMI_ID]},
                                              {'Name': 'instance-state-name', 'Values': ['running', 'pending']}])

    inst_list = []
    for inst in instances:
        inst_list.append(inst.id)
    tot_inst = len(inst_list)

    if tot_inst == 0:
        add_inst(1)

    # Get the updated details from the RDS database and feed it to the master function
    cnx = connect_to_database()
    cursor = cnx.cursor()

    query = 'SELECT * FROM autoscalar where id=1'
    cursor.execute(query)
    row = cursor.fetchone()
    cnx.commit()

    auto = row[1]
    max_thr = row[2]
    min_thr = row[3]
    add_rate = row[4]
    del_rate = row[5]
    num_add = row[6]
    num_term = row[7]

    if auto == '1':
        auto = True
    else:
        auto = False

    auto_man(auto=auto, max_thr=max_thr, min_thr=min_thr, add_rate=add_rate, del_rate=del_rate,
             num_add=num_add, num_term=num_term)

    # Take a pause of 1 minute between iterations
    time.sleep(60)
