# MIT License
# ---
# Copyright (c) 2022 Shahzeb Ihsan (https://github.com/schaazzz)

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ---

import json
import requests
import datetime
from constants import *

cred_json = {}

auth_code = ''
client_id = ''
client_secret = ''
access_token = ''
refresh_token = ''

# Get UTC time in ISO 8601 timestamp format
def get_timestamp():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

# Read credentials from the credentials file
def read_credentials():
    global cred_json
    global auth_code
    global client_id
    global client_secret
    global access_token
    global refresh_token

    with open(CREDENTIALS_PATH, 'r') as cred_file:
        cred_json = json.load(cred_file)
        auth_code = cred_json['authCode']
        client_id = cred_json['clientId']
        client_secret = cred_json['clientSecret']
        access_token = cred_json['accessToken']
        refresh_token = cred_json['refreshToken']

# Write new credentials to the credentials file
def write_credentials():
    try:
        with open(CREDENTIALS_PATH, 'w') as cred_file:
            cred_json['refreshToken'] = refresh_token
            cred_json['accessToken'] = access_token
            cred_json['lastUpdated'] = get_timestamp()
            json.dump(cred_json, cred_file, indent = 4)
            return True
    except:
        return False

# Request new Acess Token using the Refresh Token
def refresh_access_tokens():
    global access_token
    global refresh_token

    status = False

    headers = {
        'charset': 'UTF-8',
    }

    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id,
        'client_secret': client_secret
    }

    print('- Refreshing access tokens.....', end = '')

    response = requests.post(LWA_TOKEN_URI, headers = headers, data = data)
    response_json = response.json()

    if response.status_code != HTTP_RESPONSE_OK:
        print(response_json['payload']['code'] + '!')
        print(json.dumps(response_json, indent = 2))
    else:
        print('OK!')
        access_token = response_json['access_token']
        refresh_token = response_json['refresh_token']
        if write_credentials():
            print('OK!')
            status = True
        else:
            print('ERROR!\n  (Unable to parse/write credentials)')

    return status

# Request new Access and Refresh tokens
def request_access_tokens():
    global access_token
    global refresh_token

    status = False

    headers = {
        'charset': 'UTF-8',
    }

    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'client_id': client_id,
        'client_secret': client_secret
    }

    print('- Requesting access tokens.....', end = '')

    response = requests.post(LWA_TOKEN_URI, headers = headers, data = data)
    response_json = response.json()

    if response.status_code != HTTP_RESPONSE_OK:
        print(response_json['error'].upper() + '!')
        print(json.dumps(response_json, indent = 2))
    else:
        access_token = response_json['access_token']
        refresh_token = response_json['refresh_token']
        if write_credentials():
            print('OK!')
            status = True
        else:
            print('ERROR!\n  (Unable to parse/write credentials)')
    
    return status