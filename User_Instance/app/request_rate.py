import boto3
from app import updater
import threading
past_http=0
from datetime import datetime
from app.credentials import *


# import boto.utils
# meta=boto.utils.get_instance_metadata()
# id=meta['instance-id']

import urllib.request
import urllib3.request

id=urllib.request.urlopen('http://169.254.169.254/latest/meta-data/instance-id').read().decode()
id1=urllib.request.urlopen('http://169.254.169.254/latest/meta-data/instance-id').read().decode()

# print(id)
# import ec2_metadata
# id=ec2_metadata.ec2_metadata.instance_id


def req_rate():
    http = updater.http_inc() - 1
    updater.http_dec()
    print("Global_http", http)
    global past_http
    # global http
    print(http,"HTTP")
    print(past_http, "PAST_HTTP")
    http_rate=http-past_http
    past_http=http
    print(http_rate,"HTTP_RATE")
    threading.Timer(60, req_rate).start()

    client=boto3.client("cloudwatch",region_name='us-east-1',
                  aws_access_key_id=AWS_KEY_ID,
                  aws_secret_access_key=AWS_SECRET,aws_session_token=AWS_SESSION)
    response=client.put_metric_data(
        MetricData=[
            {
                "MetricName":"HTTP_RATE",
                "Dimensions": [
                    {
                        "Name":"InstanceId",
                        "Value": id
                    },
               ],
        "Timestamp":datetime.utcnow(),
        "Value":http_rate
            },
        ],
        Namespace='EC2_instance_http'
    )
    print(response)
    return ()
req_rate()

