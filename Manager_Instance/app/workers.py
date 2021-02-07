"""
-------- HOME PAGE --------

DISPLAYS THE LIST OF RUNNING INSTANCES WITH AN OPTION TO VIEW ADDITIONAL DETAILS ABOUT ANY SPECIFIC INSTANCE

DISPLAY A GRAPH WITH THE TOTAL NUMBER OF INSTANCES IN THE PAST 30 MINUTES

DISPLAYS THE MODE THE APP CURRENTLY IS IN - AUTO OR MANUAL MODE
"""


import threading
from datetime import datetime,timedelta
from app.credentials import *
from app import app
from flask import render_template, redirect, url_for, session
import mysql.connector


def connect_to_database():
    return mysql.connector.connect(user=db_config['user'],
                                   password=db_config['password'],
                                   host=db_config['host'],
                                   database=db_config['database'])


t1 = []
w_count = []

# Get the http request rate and worker count
def workers_count():
    instances = ec2.instances.filter(Filters=[{'Name': 'image-id', 'Values': [AMI_ID]},
                                              {'Name': 'instance-state-name', 'Values': ['running', 'pending']}])
    ids = []
    for idx, inst in enumerate(instances, 1):
        ids.append(inst.id)

    n = len(ids)
    w_count.append(n)

    # Log data for only 30 minutes
    if len (w_count) > 30:
        w_count.pop(0)

    t = datetime.utcnow()
    ts = t - timedelta(microseconds=t.microsecond)
    tm = ts - timedelta(seconds=ts.second)
    t1.append(tm.time())
    if len (t1) > 30:
        t1.pop(0)
    threading.Timer(60, workers_count).start()

    return w_count, t1


count, t = workers_count()


# Display list of workers with a plot of number of workers
@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'username' not in session:
        return redirect(url_for('login'))

    # To display the current status of the mode
    cnx = connect_to_database()
    cursor = cnx.cursor()

    query = 'select mode from autoscalar where id = 1'
    cursor.execute(query)
    row = cursor.fetchone()
    cnx.commit()
    cnx.close()

    auto = row[0]
    if auto == '0':
        m = "Manual mode"
    elif auto == '1':
        m = "Auto mode"
    else:
        m = ''

    instances = ec2.instances.filter(Filters=[{'Name': 'image-id', 'Values': [AMI_ID]},
                                              {'Name': 'instance-state-name', 'Values': ['running', 'pending']}])
    ids = []
    link=[]
    for idx, inst in enumerate(instances, 1):
        ids.append(inst.id)
        link.append("/parameters?id=" + inst.id)

    legend = 'WORKERS COUNT: {}'.format(count[-1])
    labels = t
    values = count

    return render_template('home.html', row=zip(ids, link), title=legend, max=8, labels=labels, values=values, m=m)
