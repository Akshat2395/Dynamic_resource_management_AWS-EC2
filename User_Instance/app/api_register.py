# -*- coding: utf-8 -*-
"""
ENDPOINT - API/REGISTER

DIRECT REGISTER
ANYONE WITH THE LINK (OF THE REGISTER API) CAN REGISTER THEMSELVES WITHOUT THE NEED OF THE ADMIN.

FIELDS REQUIRED -
1. USERNAME (unique)
2. PASSWORD (should match particular specifications)
3. RE-TYPE PASSWORD
4. REGISTER

AFTER REGISTERING, THE USER IS DIRECTED TO THE LOGIN PAGE.
"""
from flask import make_response, jsonify
from app import app
from flask import render_template,redirect,url_for,request,session, g
import bcrypt
import hashlib
from mysql import connector as mysqlconnector
from app.config import db_config
from app import global_http
from app import updater

"""   
# This method does not connect to the database somehow
def connect_to_database():
    return mysql.connector.connect(user=db_config['user'],
                                   password=db_config['password'],
                                   host=db_config['host'],
                                   database=db_config['database'],use_pure=True)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    return db

@app.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
"""

# Password should follow these rules in order to be considered valid.
rules = [lambda s: any(x.isupper() for x in s),  # must have at least one uppercase
             lambda s: any(x.islower() for x in s),  # must have at least one lowercase
             lambda s: any(x.isdigit() for x in s),  # must have at least one digit
             lambda s: len(s) >= 8, # must be at least 8 characters
             lambda s: len(s) <= 17  # must be at most 16 characters
             ]


# Display an empty HTML form that allows users to register themselves.
@app.route('/api/register',methods=['GET'])
def api_pre_register():
    updater.http_inc()
    err=''
    return render_template('api_register.html', err=err)


# After the static page is loaded, the user is prompted to register themselves by asking for their credentials.
@app.route('/api/register',methods=['POST'])
def api_register():
    updater.http_inc()
    # Reading username and passwords
    uname=request.form.get('uname',"")
    password=request.form.get('pwd',"")
    re_password=request.form.get('re_pwd',"")

    # If username field is empty, throw an error
    if uname == '':
        err = 'Enter valid username'
        servererrorcode=406
        response = make_response(
                jsonify(
                    {"success": False, "error": {"code":servererrorcode, "message": err}}
                ))
        response.headers["Content-Type"] = "application/json"
        return response
        # return render_template('api_register.html', err=err)






    # Validate the username by checking if the user exists in the database
    cnx=mysqlconnector.connect(user=db_config['user'],
                                   password=db_config['password'],
                                   host=db_config['host'],
                                   database=db_config['database'],use_pure=True)

    cursor = cnx.cursor()
            
    #Check if username already exists or not
    query = 'SELECT COUNT(1) FROM new_schema.new_table WHERE username= %s'
    cursor.execute(query,(uname,))
    row=cursor.fetchone()
    cnx.commit()
    cnx.close()
    count = row[0]

    # Throw error if username is not unique
    if count == 1:
        err='*Username already exists! Please enter a new username.'
        servererrorcode = 406
        response = make_response(
            jsonify(
                {"success": False, "error": {"code": servererrorcode, "message": err}}
            ))
        response.headers["Content-Type"] = "application/json"
        return response
        # return render_template('api_register.html', err=err)

    # Check if the passwords entered by the user matches or not
    if password == re_password:
        #err = ''
        if not all(rule(password) for rule in rules):
                err = '*Password must be at least 8 characters and comprise of one uppercase,lowercase and digit!'
                servererrorcode = 406
                response = make_response(
                    jsonify(
                        {"success": False, "error": {"code": servererrorcode, "message": err}}
                    ))
                response.headers["Content-Type"] = "application/json"
                return response
                # return render_template('api_register.html', err=err)

        cnx=mysqlconnector.connect(user=db_config['user'],
                                   password=db_config['password'],
                                   host=db_config['host'],
                                   database=db_config['database'],use_pure=True)

        cursor=cnx.cursor()
            
        # Insert user details in the database
        salt = bcrypt.gensalt()

        # Hash the passwords and save the hash in the database
        hashed_password = hashlib.pbkdf2_hmac('sha256', password.encode('ascii'), salt, 100000,dklen=16)
        hashed_password=hashed_password.hex()
        
        querry= 'INSERT INTO new_schema.new_table(username,salt,pwd_hash)VALUES(%s,%s,%s);'
        
        cursor.execute(querry,(uname,salt,hashed_password))
        
        cnx.commit()
        cnx.close()
        response = make_response(jsonify(
            {"success": True}))
        response.headers["Content-Type"] = "application/json"
        return response
        # return redirect(url_for('login'))

    # If passwords entered are not same.
    else:
        err = '*The passwords do not match!'
        servererrorcode = 406
        response = make_response(
            jsonify(
                {"success": False, "error": {"code": servererrorcode, "message": err}}
            ))
        response.headers["Content-Type"] = "application/json"
        return response
        # return render_template('api_register.html', err=err)