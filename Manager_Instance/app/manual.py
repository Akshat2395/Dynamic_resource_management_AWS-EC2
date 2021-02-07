"""
SET THE AUTOSCALAR PROPERTIES FOR MANUAL MODE

It takes number of instances to add (num_add) and number of instances to terminate (num_tern) as input from the user.

After making changes, the database is again updated with a 0 to avoid any discrepancies.
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


# Displays the number of instances/workers currently running
@app.route('/manual_mode', methods=['GET'])
def manual_mode():
    if 'username' not in session:
        return redirect(url_for('login'))

    instances = ec2.instances.filter(Filters=[{'Name': 'image-id', 'Values': [AMI_ID]},
                                              {'Name': 'instance-state-name', 'Values': ['running', 'pending']}])

    inst_list = []
    for inst in instances:
        inst_list.append(inst.id)
    tot_inst = len(inst_list)
    err = ""
    return render_template('manual.html', err=err, tot_inst=tot_inst)


# Get the number of instances to add or terminate from the user and make changes when submitted
@app.route('/manual_mode', methods=['POST'])
def manual_mode_set():
    # Get details from user
    num_add = request.form.get('num_add', '')
    num_term = request.form.get('num_term', '')
    auto = 0

    instances = ec2.instances.filter(Filters=[{'Name': 'image-id', 'Values': [AMI_ID]},
                                              {'Name': 'instance-state-name', 'Values': ['running', 'pending']}])

    inst_list = []
    for inst in instances:
        inst_list.append(inst.id)
    tot_inst = len(inst_list)

    if num_add == '':
        num_add = 0
    else:
        num_add = int(num_add)
    if num_term == '':
        num_term = 0
    else:
        num_term = int(num_term)

    if num_add > 0 and num_term > 0:
        err = "Error: you can only add or terminate an instance at once"
        return render_template('manual.html', err=err, tot_inst=tot_inst)
    else:
        if num_add + tot_inst > 8 or tot_inst - num_term < 1:
            err = "Maximum number of instances allowed is 8 and minimum number of instances allowed is 1"
            return render_template('manual.html', err=err, tot_inst=tot_inst)

    cnx = connect_to_database()
    cursor = cnx.cursor()

    query = 'UPDATE autoscalar SET mode=%s, num_add=%s, num_term=%s where id = 1'
    cursor.execute(query, (auto, num_add, num_term,))
    cnx.commit()
    cnx.close()

    # ----------------------------------------------------------------------
    # Condition to check if user provided information to only add instances
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

    # Condition to check if user provided information to only terminate instances
    if num_add == 0 and num_term > 0:
        term_inst(num_term)
        print("Manual - Terminated {} instance".format(num_term), flush=True)
        # err = "Terminated instance"

        cnx = connect_to_database()
        cursor = cnx.cursor()
        num_term = 0
        query = 'UPDATE autoscalar SET num_term=%s where id = 1'
        cursor.execute(query, (num_term,))
        cnx.commit()
        cnx.close()

        # ---------------------------------------------------------------------------------
    err = 'PARAMETERS UPDATED'
    return render_template('manual.html', err=err, tot_inst=tot_inst)
