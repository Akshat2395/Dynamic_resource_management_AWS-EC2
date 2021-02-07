# -*- coding: utf-8 -*-
"""
ENDPOINT API/UPLOAD

DIRECT REGISTER AND TEST MASK DETECTOR
ANYONE WITH THE API LINK (api/upload) CAN REGISTER THEMSELVES AND TEST OUT THE ML MODEL BY UPLOADING A VALID
PHOTO FROM THEIR SYSTEM OR BY PROVIDING A VALID WEBLINK.

"ONLY REGISTERED USERS CAN USE THIS API"

AFTER PROVIDING THE CREDENTIALS, THE USER IS TAKEN TO THE RESULTS PAGE
"""


import bcrypt
import hashlib
from app import app
import os
from flask import render_template, request, redirect, url_for, abort,session
from werkzeug.utils import secure_filename
from mysql import connector as mysqlconnector
from app import pytorch_infer
from PIL import Image
import random
import string
import requests
import cv2
from flask import jsonify, make_response
import base64
import io
import numpy as np
from os import listdir
from os.path import isfile, join
from pathlib import Path
from random import randint
from app.config import db_config
from app import global_http
from app import updater

import boto3
from app.credentials import *

# Display an empty HTML form that allows users to directly login and test the mask detection model.
@app.route('/api/upload',methods=['GET'])
def upload():
    updater.http_inc()
    return render_template('api_upload.html')


# Collect information from the forms and process them
@app.route('/api/upload',methods=['POST'])
def api_upload():
    updater.http_inc()
    # read uploaded file, username and password
    uploaded_file = request.files.get('file','')
    err=''
    uname = request.form.get('uname',"")
    password = request.form.get('pwd',"")
    
    cnx = mysqlconnector.connect(user =db_config['user'],
                           password =db_config['password'],
                           host =db_config['host'],
                           database =db_config['database'],use_pure=True)
    
    cursor = cnx.cursor()

    # Check if username already exists or not
    query = 'SELECT COUNT(1) FROM new_schema.new_table WHERE username= %s'
    cursor.execute(query,(uname,))
    row=cursor.fetchone()
    cnx.commit()

    count = row[0]

    # If count = 0, username does not exist in the database
    if count == 0:
        err = '*Invalid Username!'
        servererrorcode = 406
        response = make_response(
            jsonify(
                {"success": False, "error": {"code": servererrorcode, "message": err}}
            ))
        response.headers["Content-Type"] = "application/json"
        return response
        # return render_template('api_upload.html', err=err)
    
    # Store username in session if exists.
    session["username"]=uname

    #Checking user details for logging in
    querry = 'SELECT salt,pwd_hash From new_schema.new_table where username = %s'
    
    cursor.execute(querry,(uname,))
    row = cursor.fetchone()
    salt1 = row[0]
    encrypted_pwd = row[1]
    hashed_password = hashlib.pbkdf2_hmac('sha256', password.encode('ascii'), salt1.encode('ascii'), 100000,dklen=16)
    hashed_password = hashed_password.hex()

    # If true, user logs in
    if encrypted_pwd == hashed_password:
        cnx.close()

        webaddr = request.form.get('webaddr', '')
        if webaddr != '':
            
            app.config['MAX_CONTENT_LENGTH'] = 20*1024 * 1024
            #ext= ['jpg', 'png', 'jpeg']
            app.config['UPLOAD_PATH'] = 'app/static'

            # Check if the link  is valid and can be parsed to read the image
            try:
                img = Image.open(requests.get(webaddr, stream=True).raw).convert('RGB')
            except:
                err='Invalid Image url'
                servererrorcode = 406
                response = make_response(
                    jsonify(
                        {"success": False, "error": {"code": servererrorcode, "message": err}}
                    ))
                response.headers["Content-Type"] = "application/json"
                return response
                # return render_template("api_upload.html",err=err)


            # Check if filename can be accesed from the link, otherwise create a new name for the image
            try:
                filename = secure_filename(img.filename)
            except:
                #if filename == '':
                filename = ''.join(random.choice(string.ascii_lowercase) for i in range(10))
                filename = filename + '.jpg'
            

            #If the file name exist add random 3 digit number to the file name 
            # for i in onlyfiles:
            #     while filename == i:
            r = randint(100, 999)
            s = filename.rsplit('.',1)
            filename = s[0] + "_w_" + str(r)+"."+s[1]


            # Change to store in s3
            s3 = boto3.client("s3",
                              region_name='us-east-1',
                              aws_access_key_id=AWS_KEY_ID,
                              aws_secret_access_key=AWS_SECRET, aws_session_token=AWS_SESSION)

            img.save(os.path.join(app.config['UPLOAD_PATH'], filename))
            s3.upload_file('app/static/' + str(filename), Bucket=Bucket, Key=filename)

            path = (os.path.join(app.config['UPLOAD_PATH'], filename))
            imgp = cv2.imread(path)
            # print(path)
            os.remove(path)
            imgp = cv2.cvtColor(imgp, cv2.COLOR_BGR2RGB)
            path = imgp

            fname = filename
            # push the path of the image to the db:
            uname = session["username"]
            
            cnx = mysqlconnector.connect(user =db_config['user'],
                                       password =db_config['password'],
                                       host =db_config['host'],
                                       database =db_config['database'],use_pure=True)
            cursor = cnx.cursor()
                
            # Inserting user details and processed image details into SQL database
            querry = 'INSERT INTO history(username,img_addr,f_no,fm_no,process_img)VALUES(%s,%s,%s,%s,%s);'

            opimg, f_no, fm_no = pytorch_infer.imagepr(path)
            
            imgByteArr = io.BytesIO()
            opimg.save(imgByteArr, format='JPEG')
            
            s1 = filename.rsplit('.',1)
            filename1 = s1[0] + "_w_p_" + "." + s1[1]
            
            image_data = np.asarray(opimg)
            cv2.imwrite('app/static/'+str(filename1), cv2.cvtColor(image_data, cv2.COLOR_RGB2BGR))

            new_opimg = base64.b64encode(imgByteArr.getvalue()).decode('utf-8')
            new_opimg = u'data:img/jpeg;base64,'+ new_opimg

            s3.upload_file('app/static/' + str(filename1), Bucket=Bucket, Key=filename1)
            os.remove('app/static/' + str(filename1))

            cursor.execute(querry,(uname,fname,f_no,fm_no,filename1))
            
            cnx.commit()
            cnx.close()
            response = make_response(jsonify(
                {"success": True, "payload": {
                    "num_faces": f_no, "num_masked": fm_no, "num_unmasked": f_no - fm_no}
                 }
            )
            )
            response.headers["Content-Type"] = "application/json"
            return response
            # return render_template('Result.html',f_no=f_no,fm_no=fm_no, opimg= new_opimg)
        
        else:
            app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024
            app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.jpeg']
            app.config['UPLOAD_PATH'] = 'app/static'
            
            uploaded_file = request.files.get('file', '')

            if uploaded_file != '':
                filename = secure_filename(uploaded_file.filename)
                file_ext = os.path.splitext(filename)[1]
                if file_ext.lower() not in app.config['UPLOAD_EXTENSIONS']:
                    err="Not a valid image Selected"
                    servererrorcode = 406
                    response = make_response(
                        jsonify(
                            {"success": False, "error": {"code": servererrorcode, "message": err}}
                        ))
                    response.headers["Content-Type"] = "application/json"
                    return response
                    # return render_template("api_upload.html",err=err)
            
                # find the path of the directory
                d = Path().resolve()
                d1=str(d)+"/app/static"
                

                r=randint(100, 999)
                s = filename.rsplit('.',1)
                filename=s[0] +"_"+str(r)+"."+s[1]


                # Save Image
                path = os.path.join(app.config['UPLOAD_PATH'], filename)
                uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
                # Change to store in s3
                s3 = boto3.client("s3",
                                  region_name='us-east-1',
                                  aws_access_key_id=AWS_KEY_ID,
                                  aws_secret_access_key=AWS_SECRET, aws_session_token=AWS_SESSION)

                s3.upload_file(path, Bucket=Bucket, Key=filename)

                imgp1=cv2.imread(path)

                os.remove(path)

                imgp1= cv2.cvtColor(imgp1, cv2.COLOR_BGR2RGB)
                path=imgp1

                fname=filename
                # push the path of the image to the database
                uname=session["username"]
                
                cnx=mysqlconnector.connect(user=db_config['user'],
                                           password=db_config['password'],
                                           host=db_config['host'],
                                           database=db_config['database'],use_pure=True)
                cursor=cnx.cursor()
                    
                # INSERTING USER DETAILS INTO SQL
                querry= 'INSERT INTO history(username,img_addr,f_no,fm_no,process_img)VALUES(%s,%s,%s,%s,%s);'

                # Pass the image to image processing program
                opimg,f_no,fm_no = pytorch_infer.imagepr(path)

                imgByteArr = io.BytesIO()
                opimg.save(imgByteArr, format='JPEG')
                
                s1 = filename.rsplit('.',1)
                filename1=s1[0] +"_p"+"."+s1[1]



                image_data = np.asarray(opimg)



                cv2.imwrite('app/static/'+str(filename1), cv2.cvtColor(image_data, cv2.COLOR_RGB2BGR))
                #
                new_opimg = base64.b64encode(imgByteArr.getvalue()).decode('utf-8')
                new_opimg = u'data:img/jpeg;base64,'+ new_opimg

                s3.upload_file('app/static/'+str(filename1), Bucket=Bucket, Key=filename1)
                os.remove('app/static/'+str(filename1))

                cursor.execute(querry,(uname,fname,f_no,fm_no,filename1))
                
                cnx.commit()
                cnx.close()
                
                print(f_no,fm_no)
                response = make_response(jsonify(
                    {"success": True, "payload": {
                        "num_faces": f_no, "num_masked": fm_no, "num_unmasked": f_no-fm_no}
                     }
                )
                )
                response.headers["Content-Type"] = "application/json"
                return response
                # return render_template('Result.html',f_no=f_no,fm_no=fm_no, opimg= new_opimg)
    
    # Reload the api page with an error
    else:
        err="*WRONG CREDENTIALS"
        servererrorcode = 406
        response = make_response(
            jsonify(
                {"success": False, "error": {"code": servererrorcode, "message": err}}
            ))
        response.headers["Content-Type"] = "application/json"
        return response
        # return render_template('api_upload.html', err=err)