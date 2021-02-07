"""
SET THE AUTOSCALAR PROPERTIES FOR CREATING AND TERMINATING NEW INSTANCES

It takes maximum threshold (max_thr), minimum threshold (min_thr), add instance ratio (add_rate) and
terminate instance ratio (del_rate) as input from the user and on pressing submit, it updates the RDS with the
new details.
"""

from app import app
from flask import session, request, render_template, redirect, url_for, flash
import mysql.connector
from app.credentials import *
import mysql.connector


def connect_to_database():
    return mysql.connector.connect(user=db_config['user'],
                                   password=db_config['password'],
                                   host=db_config['host'],
                                   database=db_config['database'])

# The GET method gets the current settings/parameters which are being used by the autoscalar function.
@app.route('/auto', methods=['GET'])
def auto_mode():
    # Check if admin is logged in
    if 'username' not in session:
        return redirect(url_for('login'))

    cnx = connect_to_database()
    cursor = cnx.cursor()

    # Get all details from the RDS database
    query = 'SELECT * FROM autoscalar where id=1'
    cursor.execute(query)
    row = cursor.fetchone()

    auto = row[1]
    max_thr = row[2]
    min_thr = row[3]
    add_rate = row[4]
    del_rate = row[5]
    num_add = row[6]
    num_term = row[7]

    cnx.commit()
    cnx.close()
    err = ''
    return render_template('auto.html', err=err, max_thr=max_thr, min_thr=min_thr, add_rate=add_rate,
                           del_rate=del_rate)


# The form fields will display the values of the parameters which are currently in use.
@app.route('/auto', methods=['POST'])
def auto_mode_set():
    max_thr = request.form.get('max_thr', '')
    min_thr = request.form.get('min_thr', '')
    add_rate = request.form.get('add_rate', '')
    del_rate = request.form.get('del_rate', '')

    # Set the mode to back to 1 for automatic mode.
    auto = 1
    cnx = connect_to_database()
    cursor = cnx.cursor()

    # Update the values in the database
    query = 'UPDATE autoscalar SET mode=%s, max_thr=%s, min_thr=%s, add_rate=%s, del_rate=%s where id = 1'
    cursor.execute(query, (auto, max_thr, min_thr, add_rate, del_rate,))
    cnx.commit()
    cnx.close()
    err = 'Settings Updated!'
    return render_template('auto.html', err=err, max_thr=max_thr, min_thr=min_thr, add_rate=add_rate, del_rate=del_rate)