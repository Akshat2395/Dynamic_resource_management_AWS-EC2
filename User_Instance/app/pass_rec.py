"""
PASSWORD RECOVERY
USERS CAN RESET THEIR PASSWORDS IF THEY FORGET.
CAN BE ACCESSED FROM THE LOGIN PAGE BY CLICKING ON "Forget Password?"

1. CHECKS FOR VALID USERNAME AND EMAIL ID
2. SENDS AN OTP VIA EMAIL
3. VERIFY THE OTP SUBMITTED BY THE USER
4. USER ALLOWED TO CHANGE PASSWORD (Should adhere the rules)
5. REDIRECT TO LOGIN TO ACCESS THE APP
"""

from app import app
from flask import render_template,redirect,url_for,request,session
# from validate_email import validate_email
from mysql import connector as mysqlconnector
import re
from app.config import db_config
#from py3-validate-email
import bcrypt
import hashlib
from flask_mail import Mail, Message
import random
from app import global_http
from app import updater

otp =random.randint(000000,999999)   

# Display the HTML form for recovering password
@app.route('/pass_rec', methods=["GET"])
def pass_rec():
    updater.http_inc()
    err=""
    return render_template("pass_rec.html",err=err)     

# Read and verify username and Email
@app.route('/pass_rec',methods = ["POST"])  
def verify():
    updater.http_inc()
    mail=Mail(app)  
    app.config["MAIL_SERVER"]='smtp.gmail.com'  
    app.config["MAIL_PORT"] = 465      
    app.config["MAIL_USERNAME"] = "your_email_id"  
    app.config['MAIL_PASSWORD'] = "email_id_password" 
    app.config['MAIL_USE_TLS'] = False  
    app.config['MAIL_USE_SSL'] = True  
    mail = Mail(app)  

    uname = request.form["uname"]

    cnx=mysqlconnector.connect(user=db_config['user'],
                   password=db_config['password'],
                   host=db_config['host'],
                   database=db_config['database'],use_pure=True)
    
    cursor=cnx.cursor()

    querry="SELECT COUNT(1) FROM new_schema.new_table WHERE username= %s";
    
    cursor.execute(querry,(uname,))
    row=cursor.fetchone()
    count=row[0]
    cnx.close()
    if count==1:
         regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
         email = request.form["email"]
         valid = re.search(regex, email)
         #valid = validate_email(email, check_mx=True, verify=True, smtp_timeout=30)
         print("validity", valid)
         if valid:
             msg = Message('OTP',sender = 'username@gmail.com', recipients = [email])  
             msg.body = str(otp)  
             mail.send(msg)
             session["username"] = uname
             err=""
             return render_template('pass_ver.html')  
         else:
             err="*Invalid email"
             return render_template('pass_rec.html',err=err)  
    else:
        err="*Username not found"
        return render_template('pass_rec.html',err=err) 


# Validate the OTP
@app.route('/pass_ver',methods=["POST"])   
def validate():
    updater.http_inc()
    uname = session["username"]
    user_otp = request.form['otp'] 
    if not user_otp.isdigit():
        err="OTP should contain numbers only"
        return render_template('pass_ver.html',err=err)
    if otp == int(user_otp): 
        return  redirect(url_for('pass_change'))  
    else:
        err="OTP does not match"
        return render_template('pass_ver.html',err=err)  


# Display the webpage to enter neew password
@app.route('/pass_change')  
def pass_change():
    updater.http_inc()
    return render_template("pass_change.html") 


# Read details from the form, verify password and update the database
@app.route('/pass_change',methods=["POST"])   
def pass_change1():
   uname=session["username"]
   password=request.form.get('pwd',"")
   re_password=request.form.get('re_pwd',"")
   if password == re_password:
        #err = ''
       rules = [lambda s: any(x.isupper() for x in s),  # must have at least one uppercase
             lambda s: any(x.islower() for x in s),  # must have at least one lowercase
             lambda s: any(x.isdigit() for x in s),  # must have at least one digit
             lambda s: len(s) >= 8, # must be at least 8 characters
             lambda s: len(s) <= 17  # must be at most 17 characters
             ]
       if not all(rule(password) for rule in rules):
                err = 'Password must be at least 8 characters and comprise of one uppercase,lowercase and digit!'
                return render_template('pass_change.html', err=err)

       cnx=mysqlconnector.connect(user=db_config['user'],
                                   password=db_config['password'],
                                   host=db_config['host'],
                                   database=db_config['database'],use_pure=True)
       cursor=cnx.cursor()

        # generate salt and hash password
       salt = bcrypt.gensalt()
       hashed_password = hashlib.pbkdf2_hmac('sha256', password.encode('ascii'), salt, 100000,dklen=16)
       hashed_password=hashed_password.hex()

       querry="select uid from new_schema.new_table where username = %s;"
       querry1="UPDATE new_schema.new_table SET salt = %s, pwd_hash = %s WHERE uid = %s;" 

       cursor.execute(querry,(uname,))
       row=cursor.fetchone()
       print(row,"row")
       uid=row[0] 
       
       cursor.execute(querry1,(salt,hashed_password,uid))
       cnx.commit()
       cnx.close()
            
       return redirect(url_for('login'))

   else:
       err="password doesn't match"
       return render_template("pass_change.html",err=err)