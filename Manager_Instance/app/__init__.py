"""
INITIALIZING APP
"""

from flask import Flask

app = Flask(__name__)
app.secret_key = 'abcd'

from app import workers
from app import instance_parameters
from app import credentials
from app import login
from app import auto
from app import killall
from app import manual
from app import overall_cpu
