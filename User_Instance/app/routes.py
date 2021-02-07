"""
LOGIN PAGE
THIS IS THE FIRST AND MAIN PAGE WHEN YOU ACCESS THE WEBSITE. USERS WILL HAVE TO PROVIDE THEIR CREDENTIALS
IN ORDER TO ENTER THE APP

1. ENTER VALID USERNAME - SHOULD BE REGISTERED WITH THE APP ALREADY
2. ENTER VALID PASSWORD

Admin account credentials -
#    uname="admin"
#    password="Ece1779pass"
"""

from app import app
from flask import render_template,redirect,url_for,request,session
import hashlib
from app import global_http
from app import updater

from mysql import connector as mysqlconnector
# import mysql.connector
from app.config import db_config


# Display the login HTML file
@app.route('/')
@app.route('/login',methods=['GET'])
def login():
    updater.http_inc()
    err=""
    return render_template('login.html', err=err)


# Read and verify the login credentials provided by the user
@app.route('/login',methods=['POST'])
def check():
    updater.http_inc()
    uname=request.form.get('uname',"")
    password=request.form.get('pwd',"")

    # Check if username exists
    cnx=mysqlconnector.connect(user=db_config['user'],
                               password=db_config['password'],
                               host=db_config['host'],
                               database=db_config['database'],use_pure=True)
    cursor=cnx.cursor()

    query = 'SELECT COUNT(1) FROM new_schema.new_table WHERE username= %s'
    cursor.execute(query,(uname,))
    row=cursor.fetchone()
    cnx.commit()
    count = row[0]
    
    if count != 1:
        err='*Username does not exist!'
        return render_template('login.html', err=err)

    # CHECKING USER DETAILS FOR LOGGING IN
    querry='SELECT salt,pwd_hash From new_schema.new_table where username = %s'
    
    cursor.execute(querry,(uname,))
    row=cursor.fetchone()
    salt1=row[0]
    encrypted_pwd=row[1]
    hashed_password = hashlib.pbkdf2_hmac('sha256', password.encode('ascii'), salt1.encode('ascii'), 100000,dklen=16)
    hashed_password=hashed_password.hex()
    
    if encrypted_pwd==hashed_password :
        session["username"]=uname
        cnx.close()
        return redirect(url_for('user'))    
    else:
        cnx.close()
        err="Wrong credentials"
        return render_template('login.html',err=err, uname=uname)

# Display Login page if user logs out
@app.route('/logout')
def logout():
    updater.http_inc()
    session.pop("username", None)
    return redirect(url_for("login"))

