from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from googleapiclient.discovery import build
from oauth2client.client import AccessTokenCredentials
from google.oauth2 import id_token
from dateutil import parser
from google.auth.transport import requests
from .models import User, Error
from .util import convertDateToRFC3339, convertDateTimeToRFC3339, formulate_open_timeslots
import os.path, json, time, datetime, pytz
from pytz import timezone

routes_blueprint = Blueprint('routes', __name__)

@routes_blueprint.route('/login', methods=['POST'])
@cross_origin(supports_credentials=True)
def login():

    # Obtain id_token from request body
    data = json.loads(request.data)
    if data is None:
        raise Error('Error getting data', status_code = 400)

    user_id_token = data.get('id_token')
    if user_id_token is None:
        raise Error('Error getting id_token', status_code = 400)
    
    access_token = data.get('access_token')
    if access_token is None:
        raise Error('Error getting access_token', status_code = 400)

    # Retrieve client ID from client_secret file
    if os.path.exists(os.getcwd() + '/app/client_secret.json'):
        client_secret_path = os.getcwd() + '/app/client_secret.json'
    
    with open(client_secret_path, 'r') as client_secret_file:
        client_id = json.load(client_secret_file)['web']['client_id']
    
    try:
        # Verify token
        idinfo = id_token.verify_oauth2_token(user_id_token, requests.Request(), client_id)

        #If token issuer not from Google, return error
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Invalid token')

        # ID token is valid. Query database for user email and create account if necessary
        split_user_name = idinfo['name'].split(' ')
        user = User.objects(email=idinfo['email']).first()
        if user is None:
            user = User(first_name = split_user_name[0], last_name = split_user_name[1], email = idinfo['email'], access_token = access_token).save()
        else:
            user.access_token = access_token    # Refresh access_token
            user.save()
        return user.toJSON(), 200

    except ValueError as e:
        # Invalid token
        raise Error(e, status_code = 400)

@routes_blueprint.route('/free_intervals/id=<id>')
@cross_origin(supports_credentials=True)
def get_free_intervals(id):
    user = User.objects(user_id = id).first()
    if not user:
        raise Error("No existing user with the associated user ID", status_code = 400)
    else:
        access_token = user.access_token
    
    
    credentials = AccessTokenCredentials(access_token, 'my-user-agent/1.0')


    try: 
        service = build('calendar', 'v3', credentials=credentials)

        local_timezone = timezone('US/Pacific')
        now = datetime.datetime.now(tz=local_timezone)
        today = now.date()
        today_7am = local_timezone.localize(datetime.datetime.combine(today, datetime.time(7,0)))
        tomorrow = today + datetime.timedelta(days=1)
        tomorrow_start = local_timezone.localize(datetime.datetime.combine(tomorrow, datetime.time(0,0)))

        events_result = service.events().list(calendarId='primary', timeMin=convertDateTimeToRFC3339(today_7am), timeMax=convertDateTimeToRFC3339(tomorrow_start), singleEvents=True, orderBy='startTime').execute()
        if not events_result:
            raise ValueError("Could not get events from Calendar API", status_code = 500)
        events = events_result.get('items', [])

        return jsonify([timeslot.__dict__ for timeslot in formulate_open_timeslots(events, today)]), 200


    except ValueError as e:
        raise Error(e, status_code = 500)
    
    except Exception as e:
        raise Error("Could not connect to calendar API, perhaps due to invalid credentials/access_token --> Returned Error: {}".format(e), status_code = 400)

    

@routes_blueprint.route('/calendar/id=<id>&start=<start_date>&end=<end_date>', methods=['GET'])
@cross_origin(supports_credentials=True)
def return_calendar_data(id, start_date, end_date):

    # Extract Access Token from Authorization heeader
    user = User.objects(user_id = id).first()
    if not user:
        raise Error("No existing user with the associated user ID", status_code = 400)
    else:
        access_token = user.access_token

    # Extract date from query string params, and switch to UTC time, and then to RFC 3339 format for Google API
    start_datetime = convertDateToRFC3339(start_date)
    end_datetime = convertDateToRFC3339(end_date)

    # Build credentials object from access_token
    credentials = AccessTokenCredentials(access_token, 'my-user-agent/1.0')

    # Try to get events from Calendar API between start_date and end_date
    try: 
        service = build('calendar', 'v3', credentials=credentials)

        events_result = service.events().list(calendarId='primary', timeMin=start_datetime, timeMax=end_datetime,
                                    singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            raise ValueError("Could not get events from Calendar API", status_code = 500)
        else:
            return jsonify(events), 200

    except ValueError as e:
        raise Error(e, status_code = 500)

    except Exception as e:
        raise Error("Could not connect to calendar API, perhaps due to invalid credentials/access_token --> Returned Error: {}".format(e), status_code = 400)


@routes_blueprint.errorhandler(Error)
def handle_error(e):
    response = jsonify(e.to_dict())
    response.status_code = e.status_code
    return response
