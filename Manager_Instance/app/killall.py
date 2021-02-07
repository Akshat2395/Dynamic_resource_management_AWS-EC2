"""
PERFORMS A SYSTEM-WIDE KILL OPERATION
- UNREGISTERS FROM ELB AND TERMINATES ALL INSTANCES
- DELETES ALL THE CONTENTS OF THE S3 BUCKET
- DELETES ALL OF THE USER DATA - LOGIN CREDENTIALS AND UPLOAD HISTORY
- STOPS THE MANAGER INSTANCE
"""

from app import app
from flask import session, request, render_template, redirect, url_for
import mysql.connector
from app.credentials import *


def connect_to_database():
    return mysql.connector.connect(user=db_config['user'],
                                   password=db_config['password'],
                                   host=db_config['host'],
                                   database=db_config['database'])


def connect_to_database_u():
    return mysql.connector.connect(user=db_config2['user'],
                                   password=db_config2['password'],
                                   host=db_config2['host'],
                                   database=db_config2['database'])

# KILL ALL - Submit for confirmation
@app.route('/kill_all', methods=['GET'])
def killall1():
    if 'username' not in session:
        return redirect(url_for('login'))

    return render_template('killall.html')


@app.route('/kill_all', methods=['POST'])
def killall():
    instances = ec2.instances.filter(Filters=[{'Name': 'image-id', 'Values': [AMI_ID]},
                                              {'Name': 'instance-state-name', 'Values': ['running', 'pending']}])

    auto = 0
    cnx = connect_to_database()
    cursor = cnx.cursor()

    # Change mode to manual so that the autoscalar function cannot add new instances
    query = 'UPDATE autoscalar SET mode = %s where id = 1'
    cursor.execute(query, (auto,))
    cnx.commit()
    cnx.close()

    ids = []
    for inst in instances:
        ids.append(inst.id)

    # Delete contents of S3
    bucket = s3.Bucket('tb1779-a2')
    bucket.objects.all().delete()

    # DELETE USER CREDENTIALS
    cnx = connect_to_database_u()
    cursor = cnx.cursor()

    query2 = 'DELETE FROM new_table'
    cursor.execute(query2)
    cnx.commit()
    cnx.close()

    # DELETE HISTORY DATA
    cnx = connect_to_database_u()
    cursor = cnx.cursor()

    query3 = 'DELETE FROM history'
    cursor.execute(query3)
    cnx.commit()
    cnx.close()

    # Terminate all running instances
    term_inst(len(ids))

    # Stop the manager app
    ids = ['i-0d67d23f1c9ff316a']
    ec2.instances.filter(InstanceIds=ids).stop()

    return
