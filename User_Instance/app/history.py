# -*- coding: utf-8 -*-
"""
DISPLAY HISTORY - PREVIOUSLY SEARCHED IMAGES

Categorize the images in 4 segments and display them.
"""

from app import app
from flask import render_template,redirect,url_for,request,session
from mysql import connector as mysqlconnector
from app.config import db_config
from app.credentials import *
from app import global_http
from app import updater
# Check sessions for the same username and display the HTML
@app.route('/history',methods=['GET'])
def history1():
    updater.http_inc()
    if 'username' not in session:    
        return redirect(url_for('login'))    
    else:
        uname=session["username"]
        return render_template('history1.html')


# Get details from the form submitted by the user
@app.route('/history',methods=['POST'])
def history():
    updater.http_inc()
    if 'username' not in session:    
        return redirect(url_for('login'))    
    else:
        uname=session["username"]
        cnx=mysqlconnector.connect(user=db_config['user'],
                               password=db_config['password'],
                               host=db_config['host'],
                               database=db_config['database'],use_pure=True)
        
        cursor=cnx.cursor()
                
        # Get the set of images according to the conditions
        querry='SELECT img_addr,process_img From new_schema.history where username = %s and f_no=fm_no and f_no>0'
        querry1='SELECT img_addr,process_img From new_schema.history where username = %s and f_no= 0'
        querry2='SELECT img_addr,process_img From new_schema.history where username = %s and f_no>0 and fm_no=0'
        querry3='SELECT img_addr,process_img From new_schema.history where username = %s and fm_no>0 and f_no > fm_no'
        
        cursor.execute(querry,(uname,))
        row=cursor.fetchall()
        
        cursor.execute(querry1,(uname,))
        row1=cursor.fetchall()
        
        cursor.execute(querry2,(uname,))
        row2=cursor.fetchall()
        
        cursor.execute(querry3,(uname,))
        row3=cursor.fetchall()      
        
        cnx.close()
        import boto3

        s3 = boto3.resource("s3",
                            region_name='us-east-1',
                            aws_access_key_id=AWS_KEY_ID,
                            aws_secret_access_key=AWS_SECRET, aws_session_token=AWS_SESSION)
        s3_client = boto3.client("s3",
                                 region_name='us-east-1',
                                 aws_access_key_id=AWS_KEY_ID,
                                 aws_secret_access_key=AWS_SECRET, aws_session_token=AWS_SESSION)

        # Your Bucket Name
        bucket = s3.Bucket(Bucket)

        # Gets the list of objects in the Bucket
        s3_Bucket_iterator = bucket.objects.all()

        # Generates the Signed URL for each object in the Bucket




        opt=request.form.get('options',"")

        # Display images corresponding to each category
        # if opt == "1":
        #     info='Images where all faces are wearing mask'
        #     return render_template('history.html',row=row, info=info)
        if opt == "1":
            info='Images where all faces are wearing mask'
            lst1 = []
            lst2 = []

            for j in row:
                for i in s3_Bucket_iterator:
                    if i.key == j[0]:
                        url = s3_client.generate_presigned_url(ClientMethod='get_object',
                                                               Params={'Bucket': bucket.name, 'Key': i.key})

                        lst1.append(url)
                    if i.key == j[1]:
                        url = s3_client.generate_presigned_url(ClientMethod='get_object',
                                                               Params={'Bucket': bucket.name, 'Key': i.key})

                        lst2.append(url)
            lst1 = lst1[::-1]
            lst2 = lst2[::-1]
            return render_template('history.html',row=zip(lst1,lst2), info=info)
        if opt== "2":
            info = 'Images with no face detected'
            lst1 = []
            lst2 = []

            for j in row1:
                for i in s3_Bucket_iterator:
                    if i.key == j[0]:
                        url = s3_client.generate_presigned_url(ClientMethod='get_object',
                                                               Params={'Bucket': bucket.name, 'Key': i.key})

                        lst1.append(url)
                    if i.key == j[1]:
                        url = s3_client.generate_presigned_url(ClientMethod='get_object',
                                                               Params={'Bucket': bucket.name, 'Key': i.key})

                        lst2.append(url)
            lst1 = lst1[::-1]
            lst2 = lst2[::-1]
            return render_template('history.html',row=zip(lst1,lst2), info=info)
        if opt=="3":
            info = 'Images where all faces are not wearing mask'
            lst1 = []
            lst2 = []

            for j in row2:
                for i in s3_Bucket_iterator:
                    if i.key == j[0]:
                        url = s3_client.generate_presigned_url(ClientMethod='get_object',
                                                               Params={'Bucket': bucket.name, 'Key': i.key})

                        lst1.append(url)
                    if i.key == j[1]:
                        url = s3_client.generate_presigned_url(ClientMethod='get_object',
                                                               Params={'Bucket': bucket.name, 'Key': i.key})

                        lst2.append(url)
            lst1 = lst1[::-1]
            lst2 = lst2[::-1]
            return render_template('history.html',row=zip(lst1,lst2), info=info)
        if opt=="4":
            info = 'Images with some face wearing mask'
            lst1 = []
            lst2 = []

            for j in row3:
                for i in s3_Bucket_iterator:
                    if i.key == j[0]:
                        url = s3_client.generate_presigned_url(ClientMethod='get_object',
                                                               Params={'Bucket': bucket.name, 'Key': i.key})

                        lst1.append(url)
                    if i.key == j[1]:
                        url = s3_client.generate_presigned_url(ClientMethod='get_object',
                                                               Params={'Bucket': bucket.name, 'Key': i.key})

                        lst2.append(url)
            lst1=lst1[::-1]
            lst2=lst2[::-1]
            return render_template('history.html',row=zip(lst1,lst2), info=info)