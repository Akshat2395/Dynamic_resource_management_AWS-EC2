"""
DELETE USERS - ACCESSED ONLY BY ADMIN

THIS SHOWS A LIST OF USERS AS A DROPDOWN WHERE THE ADMIN CAN SELECT A USER AND DELETE HIS ACCOUNT FROM THE
DATABASE.
"""

from app import app
from flask import render_template, redirect, url_for, request, session
import bcrypt
import hashlib
from mysql import connector as mysqlconnector
from app.config import db_config
from app import global_http
from app import updater

# Show the list of all usernames except for admin (cannot delete itself)
@app.route('/delete', methods=['GET'])
def delete1():
    updater.http_inc()
    cnx = mysqlconnector.connect(user=db_config['user'],
                                  password=db_config['password'],
                                  host=db_config['host'],
                                  database=db_config['database'], use_pure=True)

    cursor = cnx.cursor()

    # Get usernames of al the users registered with the app
    query = 'SELECT username FROM new_schema.new_table WHERE username != "admin";'
    cursor.execute(query)
    row = cursor.fetchall()
    err=''
    return render_template('delete.html', err=err, row=row)

# Get details from the form - username selected by the admin
@app.route('/delete', methods=['POST'])
def delete():
    updater.http_inc()
    if 'username' in session:
        if session["username"] != "admin":
            return redirect(url_for('login'))
        else:
            uname = request.form.get('uname', "")

            # If username selected by the admin does not exist - failsafe
            if uname == '':
                err = 'Enter valid username'
                return render_template('delete.html', err=err)

            cnx = mysqlconnector.connect(user=db_config['user'],
                                          password=db_config['password'],
                                          host=db_config['host'],
                                          database=db_config['database'], use_pure=True)

            cursor = cnx.cursor()

            # Check if username already exists or not
            query = 'SELECT COUNT(1) FROM new_schema.new_table WHERE username= %s'
            cursor.execute(query, (uname,))
            row = cursor.fetchone()
            count = row[0]

            if count != 1:
                err = "Username does not exist"
                return render_template('delete.html', err=err)

            else:
                query1 = 'DELETE FROM new_schema.new_table where username = %s'
                cursor.execute(query1, (uname,))
                cnx.commit()
                cnx.close()

                return redirect(url_for('user'))