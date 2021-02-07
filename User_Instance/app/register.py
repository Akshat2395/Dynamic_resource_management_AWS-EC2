# -*- coding: utf-8 -*-
"""
CREATE NEW USER - ACCESSED ONLY BY ADMIN

ADMIN ENTERS UNIQUE USERNAME AND PASSWORD TO CREATE A NEW USER.
"""

from app import app
from flask import render_template,redirect,url_for,request,session
import bcrypt
import hashlib
from mysql import connector as mysqlconnector
from app.config import db_config
from app import global_http
from app import updater

rules = [lambda s: any(x.isupper() for x in s),  # must have at least one uppercase
             lambda s: any(x.islower() for x in s),  # must have at least one lowercase
             lambda s: any(x.isdigit() for x in s),  # must have at least one digit
             lambda s: len(s) >= 8, # must be at least 8 characters
             lambda s: len(s) <= 17  # must be at most 16 characters
             ]


# Display html to admin to fill out the new user details
# Check if the website was accessed by admin or not
@app.route('/register',methods=['GET'])
def pre_register():
    updater.http_inc()
    if 'username' in session:
        if session["username"] != "admin":
            return redirect(url_for('login'))
        else:
            err=''
            return render_template('new_user.html', err=err)


# Read credentials submitted by the admin
@app.route('/register',methods=['POST'])
def register():
    updater.http_inc()
    if 'username' in session:
        if session["username"] != "admin":
            return redirect(url_for('login'))
        else:
            uname=request.form.get('uname',"")
            password=request.form.get('pwd',"")

            # Check if username is provided
            if uname == '':
                err='Enter valid username'
                return render_template('new_user.html', err=err)

            # Check if password matches the set of rules
            if not all(rule(password) for rule in rules):
                err = 'Password must be at least 8 characters and comprise of one uppercase,lowercase and digit!'
                return render_template('new_user.html', err=err)
            
            
            cnx=mysqlconnector.connect(user=db_config['user'],
                                       password=db_config['password'],
                                       host=db_config['host'],
                                       database=db_config['database'],use_pure=True)
            
            cursor=cnx.cursor()
            
            #Check if username already exists or not
            query = 'SELECT COUNT(1) FROM new_schema.new_table WHERE username= %s'
            cursor.execute(query,(uname,))
            row=cursor.fetchone()
            count=row[0]
            cnx.close()
            
            if count == 1:
                err='Username already exists! Please enter a new username.'
                return render_template('new_user.html', err=err)
            else:
                # INSERTING USER DETAILS INTO SQL
                salt = bcrypt.gensalt()
                hashed_password = hashlib.pbkdf2_hmac('sha256', password.encode('ascii'), salt, 100000,dklen=16)
                hashed_password=hashed_password.hex()

                cnx = mysqlconnector.connect(user=db_config['user'],
                                              password=db_config['password'],
                                              host=db_config['host'],
                                              database=db_config['database'], use_pure=True)
                cursor=cnx.cursor()
                
                querry= 'INSERT INTO new_table(username,salt,pwd_hash)VALUES(%s,%s,%s);'
                
                cursor.execute(querry,(uname,salt,hashed_password))
                cnx.commit()
                cnx.close()
                    
                return redirect(url_for('user'))

    # if username in session is not admin
    else:
        return redirect(url_for('login'))



