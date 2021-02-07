"""
PROVIDE CPU UTILIZATION DATA AND HTTP REQUESTS OF EVERY RUNNING INSTANCE
"""

from app import app
from flask import render_template,redirect,url_for,request,session
from app.credentials import *
from datetime import datetime, timedelta


# Get the instance Id selected
@app.route('/parameters', methods=['GET'])
def parameters1():
    if 'username' not in session:
        return redirect(url_for('login'))
    else:
        id = request.args.get('id')
        session['id'] = id
    return render_template('parameters1.html')


# For the selected instance, show the http requests count and CPU utilization.
@app.route('/parameters', methods=['POST'])
def parameters():
    id = session['id']

    # Get CPU utilization data from cloudwatch
    response = stats.get_metric_data(
        MetricDataQueries=[
            {
                'Id': 'string',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/EC2',
                        'MetricName': 'CPUUtilization',
                        'Dimensions': [
                            {
                                'Name': 'InstanceId',
                                'Value': id,
                            },
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Average',
                    'Unit': 'Percent'
                },
                "Label": "myRequestLabel",
                "ReturnData": True
            },
        ],
        StartTime=datetime.utcnow() - timedelta(hours=1),
        EndTime=datetime.utcnow()
    )

    data = response["MetricDataResults"][0]

    # Get HTTP request rate data from cloudwatch
    response1 = stats.get_metric_data(
        MetricDataQueries=[
            {
                'Id': 'string',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'EC2_instance_http',
                        'MetricName': 'HTTP_RATE',
                        'Dimensions': [
                            {
                                'Name': 'InstanceId',
                                'Value': id
                            },
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Average',
                    'Unit': 'None'
                },
                "Label": "myRequestLabel",
                "ReturnData": True
            },
        ],
        StartTime=datetime.utcnow() - timedelta(hours=1),
        EndTime=datetime.utcnow()
    )

    data1 = response1["MetricDataResults"][0]

    legend = 'CPU UTILIZATION (UTC)'
    labels = data['Timestamps'][::-1]
    l = []
    for i in labels:
        l.append(i.time())
    values = data["Values"][::-1]

    legend1 = 'HTTP REQUEST RATE'
    labels1 = data1['Timestamps'][::-1]
    l1 = []
    for i in labels1:
        l1.append(i.time())
    values1 = data1["Values"][::-1]

    opt = request.form.get('options', "")
    if opt == "1":
        return render_template('line_plot.html', title=legend, max=100, labels=l, values=values)
    if opt == "2":
        return render_template('line_plot.html', title=legend1, max=100, labels=l1, values=values1)



