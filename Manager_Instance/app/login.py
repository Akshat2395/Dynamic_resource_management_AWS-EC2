"""
USER PROVIDES CERTAIN CREDENTIALS TO ACCESS THE MANAGER APP
"""

from app import app
from flask import session, request, render_template, redirect, url_for, flash

# LOGIN PAGE
@app.route('/')
@app.route('/login', methods=['GET'])
def login():
    err = ''
    return render_template('login.html', err=err)


@app.route('/login', methods=['POST'])
def check():
    uname = request.form.get('uname', '')
    password = request.form.get('pwd', '')

    if uname == 'admin' and password == 'admin':
        session['username'] = uname
        return redirect(url_for('home'))

    else:
        err = 'Invalid Login!'
        return render_template('login.html', err=err)


# Logout user
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))
