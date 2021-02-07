"""
REDUNDANT PAGE JUST TO SEE THE OVERALL CPU UTILIZATION BY ALL THE INSTANCES

- No Login required
"""

from app import app
from app.credentials import *
from datetime import datetime, timedelta
import threading
from flask import render_template


tot_cpu = []
t1 = []

# Get the average CPU usage by all instances and plot the values for the past 30 minutes.
def cpu():

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

    tot_cpu.append(average_load)
    if len(tot_cpu) > 30:
        tot_cpu.pop(0)
    t = datetime.utcnow()
    ts = t - timedelta(microseconds=t.microsecond)
    tm = ts - timedelta(seconds=ts.second)
    t1.append(tm.time())
    if len(t1) > 30:
        t1.pop(0)
    threading.Timer(60, cpu).start()

    return tot_cpu, t1

a, b = cpu()


@app.route('/cpu', methods=['GET'])
def overall_cpu():
    legend = 'Overall CPU Usage'
    labels = b
    values = a
    return render_template('overall_cpu.html', title=legend, max=100, labels=labels, values=values)