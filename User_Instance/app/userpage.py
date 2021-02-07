# -*- coding: utf-8 -*-
"""
USER PAGE - HOME PAGE

AFTER LOGGING IN OR CLICKING AT HOME FROM ANYWHERE IN THE APP, THE USER IS REDIRECTED THE USER/HOME PAGE.

USERS CAN EITHER UPLOAD A VALID PHOTO FROM THEIR LOCAL FILE SYSTEM OR VALID A WEBLINK OF THE IMAGE.

USERS CAN ALSO ACCESS THEIR GALLERY - WHICH IS THE PAST UPLOADS.

USERS CAN ALSO CHANGE THEIR PASSWORD FROM THIS PAGE IF THEY WANT TO.

*ADMIN PRIVILEGES:* - DISPLAYED TO ADMIN ONLY
ADMIN HAS THE OPTION TO CREATE A NEW USER ACCOUNT AND DELETE AN EXISTING USER ACCOUNT.
THESE FUNCTIONS CAN BE ACCESSED FROM THIS PAGE.
"""

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
import PIL
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
from app.credentials import *
from app import global_http
from app import updater
import boto3




app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.jpeg']
app.config['UPLOAD_PATH'] = 'app/static'


# Display user page HTML
@app.route('/user',methods=['GET'])
def user():
    updater.http_inc()

    if 'username' in session:
        uname=session["username"]
        return render_template('user.html',uname=uname)
    else:
        return redirect(url_for('login'))

# Receive form details from the user
@app.route('/user',methods=['POST'])
def user1():
    updater.http_inc()
    app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024
    app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.jpeg']
    app.config['UPLOAD_PATH'] = 'app/static'
    uname = session['username']

    uploaded_file = request.files.get('file', '')

    # EITHER UPLOAD IMAGE OR ENTER WEBLINK

    # Check for errors in filename and images uploaded
    if uploaded_file != '':
        filename = secure_filename(uploaded_file.filename)
        file_ext = os.path.splitext(filename)[1]
        if file_ext.lower() not in app.config['UPLOAD_EXTENSIONS']:
            err="Not a valid image Selected"
            return render_template("user.html",err=err, uname=uname)
        

        r=randint(100, 999)
        s = filename.rsplit('.',1)
        filename=s[0] +"_"+str(r)+"."+s[1]



        path = os.path.join(app.config['UPLOAD_PATH'], filename)
        uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))

        # Change to store in s3
        s3 = boto3.client("s3",
                          region_name='us-east-1',
                          aws_access_key_id=AWS_KEY_ID,
                          aws_secret_access_key=AWS_SECRET, aws_session_token=AWS_SESSION)

        s3.upload_file(path, Bucket=Bucket, Key=filename)

        imgp1 = cv2.imread(path)

        os.remove(path)
        imgp1 = cv2.cvtColor(imgp1, cv2.COLOR_BGR2RGB)
        path = imgp1


        fname=filename

        # push the path of the image to the db:
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
        
        new_opimg = base64.b64encode(imgByteArr.getvalue()).decode('utf-8')
        new_opimg = u'data:img/jpeg;base64,'+ new_opimg

        s3.upload_file('app/static/' + str(filename1), Bucket=Bucket, Key=filename1)
        os.remove('app/static/' + str(filename1))

        cursor.execute(querry,(uname,fname,f_no,fm_no,filename1))
        
        cnx.commit()
        cnx.close()
        
        print(f_no,fm_no)
        return render_template('Result.html',f_no=f_no,fm_no=fm_no, opimg= new_opimg)

    # If provided weblink
    else:
        webaddr = request.form.get('webaddr', '')

        # Check if weblink field is empty
        if webaddr == '':
            err="No image Selected"
            return render_template("user.html",err=err, uname=uname)

        # Check if weblink is valid
        if webaddr != '':
            app.config['MAX_CONTENT_LENGTH'] = 20*1024 * 1024
            ext= ['jpg', 'png', 'jpeg']
            app.config['UPLOAD_PATH'] = 'app/static'
            
            if "." not in webaddr:
                 err="Not a valid link"
                 return render_template('user.html',err=err, uname=uname)
            x = webaddr.rsplit(".", 1)
            right=x[1]
            y=right.rsplit("?",1)
            y=y[0]  

            # Check if weblink has a valid image extension
            if y.lower() not in ext:
                err="Not a valid Image"
                return render_template('user.html',err=err, uname=uname)
            
            else:
                # Read/Download the image from weblink
                try:
                    img = Image.open(requests.get(webaddr, stream=True).raw)
                except:
                    err='Invalid Image url'
                    return render_template('user.html',err=err, uname=uname)


                filename = secure_filename(img.filename)
                
                if filename == '':
                    filename = ''.join(random.choice(string.ascii_lowercase) for i in range(10))
                    filename = filename + '.jpg'

                r=randint(100, 999)
                s = filename.rsplit('.',1)
                filename=s[0] +"_w_"+str(r)+"."+s[1]
                

                # Change to store in s3
                s3 = boto3.client("s3",
                                  region_name='us-east-1',
                                  aws_access_key_id=AWS_KEY_ID,
                                  aws_secret_access_key=AWS_SECRET, aws_session_token=AWS_SESSION)

                img.save(os.path.join(app.config['UPLOAD_PATH'], filename))
                s3.upload_file('app/static/' + str(filename), Bucket=Bucket, Key=filename)

                path=(os.path.join(app.config['UPLOAD_PATH'], filename))
                imgp = cv2.imread(path)

                os.remove(path)
                imgp = cv2.cvtColor(imgp, cv2.COLOR_BGR2RGB)
                path = imgp



                fname=filename

                # push the path of the image to the db:
                uname=session["username"]
                
                cnx=mysqlconnector.connect(user=db_config['user'],
                                           password=db_config['password'],
                                           host=db_config['host'],
                                           database=db_config['database'],use_pure=True)
                cursor=cnx.cursor()
                    
                # INSERTING USER DETAILS INTO SQL
                querry= 'INSERT INTO history(username,img_addr,f_no,fm_no,process_img)VALUES(%s,%s,%s,%s,%s);'

                opimg,f_no,fm_no = pytorch_infer.imagepr(path)

                # Convert output image to flask-readable file
                imgByteArr = io.BytesIO()
                opimg.save(imgByteArr, format='JPEG')
                
                s1 = filename.rsplit('.',1)
                filename1=s1[0] +"_w_p_"+"."+s1[1]

                image_data = np.asarray(opimg)
                cv2.imwrite('app/static/'+str(filename1), cv2.cvtColor(image_data, cv2.COLOR_RGB2BGR))

                new_opimg = base64.b64encode(imgByteArr.getvalue()).decode('utf-8')
                new_opimg = u'data:img/jpeg;base64,'+ new_opimg

                s3.upload_file('app/static/' + str(filename1), Bucket=Bucket, Key=filename1)
                os.remove('app/static/' + str(filename1))

                cursor.execute(querry,(uname,fname,f_no,fm_no,filename1))
                
                cnx.commit()
                cnx.close()

                return render_template('Result.html',f_no=f_no,fm_no=fm_no, opimg= new_opimg)
        
    

