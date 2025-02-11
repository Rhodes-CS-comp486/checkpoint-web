from logging import raiseExceptions
from flask import Flask, render_template, request, redirect, url_for

import datetime

app = Flask(__name__)

# Routes
@app.route('/', methods=['POST', 'GET'])
def home():
    return render_template('index.html')