from flask import Flask, request, jsonify, session, redirect, url_for, escape, render_template
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from mongoengine import connect
from models import User
from googleapiclient.discovery import build
from oauth2client import client
from google.oauth2 import id_token
from google.auth.transport import requests


import os.path
import json


class Response:
    def __init__(self, code, message):
        self.response_code = code
        self.response_message = message 
    
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'randomkey'
app.debug = True

connect(db = 'task-scheduler',
    username = 'admin',
    password = 'adminpassword',
    host =  'mongodb://admin:adminpassword@task-scheduler-shard-00-00-x34zf.azure.mongodb.net:27017,task-scheduler-shard-00-01-x34zf.azure.mongodb.net:27017,task-scheduler-shard-00-02-x34zf.azure.mongodb.net:27017/test?ssl=true&replicaSet=task-scheduler-shard-0&authSource=admin&retryWrites=true')

@app.route('/')
def index():
    return "Base route"
    

@app.route('/login', methods=['POST'])
def login():
    # Obtain authorization code and id_token from request body
    data = request.data
    data = json.loads(data)
    authorization_code = data['auth_code']
    token = data['id_token']

    
    # Retrieve client ID from client_secret file
    if os.path.exists(os.getcwd() + '/client_secret.json'):
        client_secret_path = os.getcwd() + '/client_secret.json'
    
    with open(client_secret_path, 'r') as client_secret_file:
        client_id = json.load(client_secret_file)['web']['client_id']
    
    try:
        # Verify token
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), client_id)

        #If token issuer not from Google, return error
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer')

        # ID token is valid. Query database for user email and create account if necessary
        user = User.objects(email=idinfo['email']).first()
        if user is None:
            user = User(idinfo['name'].split(' ')[0], idinfo['name'].split(' ')[1], idinfo['email']).save()
    
        return jsonify(user)
    except ValueError:
        # Invalid token
        return Reponse(301, "Error: token is invalid").toJSON()

    

    """
    # Retrieve credentials from authorization code 
    scopes = ['https://www.googleapis.com/auth/calendar']
    credentials = client.credentials_from_clientsecrets_and_code(client_secret_path, scopes, code)
    return jsonify(credentials)
    """

    
    

@app.route('/calendar', methods=['GET'])
def return_calendar_data():

    code = request.headers.get('code')
    scopes = ['https://www.googleapis.com/auth/calendar']
    credentials = client.credentials_from_clientsecrets_and_code(client_secret_path, scopes, code)

    service = build('calendar', 'v3', credentials=credentials)

    events = service.events().list(calendarId='primary', timeMin=now, maxResults=10)

    return jsonify(events)



@app.route('/logout')
def logout():
    logout_user()
    return Reponse(200, "User logged out.").toJSON()
