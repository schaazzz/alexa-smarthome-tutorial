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


import sys
import json
import boto3
import requests
import datetime

HTTP_RESPONSE_OK = 200
HTTP_RESPONSE_ACCEPTED = 202

ALEXA_REGION = 'eu-west-1'

DOORBELL_ENDPOINT_ID = 'sample-doorbell-01'

CRED_PATH = "..\\..\\.credentials"

LWA_TOKEN_URI = 'https://api.amazon.com:443/auth/o2/token'

ALEXA_EVENT_GATEWAY_EU = 'https://api.eu.amazonalexa.com/v3/events'
ALEXA_EVENT_GATEWAY_NA = 'https://api.amazonalexa.com/v3/events'
ALEXA_EVENT_GATEWAY_FE = 'https://api.fe.amazonalexa.com/v3/events'

cred_json = {}

event_gateway = ''

auth_code = ''
client_id = ''
client_secret = ''
access_token = ''
refresh_token = ''

def get_timestamp():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def read_creds():
    global cred_json
    global auth_code
    global client_id
    global client_secret
    global access_token
    global refresh_token

    with open(CRED_PATH, 'r') as cred_file:
        cred_json = json.load(cred_file)
        auth_code = cred_json['authCode']
        client_id = cred_json['clientId']
        client_secret = cred_json['clientSecret']
        access_token = cred_json['accessToken']
        refresh_token = cred_json['refreshToken']

def write_creds():
    try:
        with open(CRED_PATH, 'w') as cred_file:
            cred_json['refreshToken'] = refresh_token
            cred_json['accessToken'] = access_token
            cred_json['lastUpdated'] = get_timestamp()
            json.dump(cred_json, cred_file, indent = 4)
            return True
    except:
        return False

def trigger_doorbell():
    headers = {
        'Content-Type': 'application/json',
    }

    json_data = {
        'context': {},
        'event': {
            'header': {
                'messageId': '9eac4fa2-9de0-4e75-ac38-9dde79abb1bd',
                'namespace': 'Alexa.DoorbellEventSource',
                'name': 'DoorbellPress',
                'payloadVersion': '3',
            },
            'endpoint': {
                'scope': {
                    'type': 'BearerToken',
                    'token': access_token,
                },
                'endpointId': DOORBELL_ENDPOINT_ID,
            },
            'payload': {
                'cause': {
                    'type': 'PHYSICAL_INTERACTION',
                },
                'timestamp': get_timestamp(),
            },
        },
    }

    print('- Sending doorbell event.......', end = '')

    response = requests.post(
        event_gateway + '?Authorization=Bearer ' + access_token,
        headers = headers,
        json=json_data,
    )

    if response.status_code != HTTP_RESPONSE_ACCEPTED:
        response_json = response.json()
        print(response_json['payload']['code'] + '!')

        if response_json['payload']['code'] == 'INVALID_ACCESS_TOKEN_EXCEPTION':
            refresh_access_tokens()
        else:
            print(json.dumps(response_json, indent = 2))
    else:
        print('OK!')

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
    print(response)
    print(response_json)
    if response.status_code != HTTP_RESPONSE_OK:
        print(response_json['payload']['code'] + '!')
        print(json.dumps(response_json, indent = 2))
    else:
        print('OK!')
        access_token = response_json['access_token']
        refresh_token = response_json['refresh_token']
        if write_creds():
            print('OK!')
            status = True
        else:
            print('ERROR!\n  (Unable to parse/write credentials)')

    return status

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
        if write_creds():
            print('OK!')
            status = True
        else:
            print('ERROR!\n  (Unable to parse/write credentials)')
    
    return status

if __name__ == '__main__':
    if ALEXA_REGION == 'eu-west-1':
        event_gateway = ALEXA_EVENT_GATEWAY_EU
    
    if ALEXA_REGION == 'us-east-1':
        event_gateway = ALEXA_EVENT_GATEWAY_NA

    if ALEXA_REGION == ' us-west-2':
        event_gateway = ALEXA_EVENT_GATEWAY_FE

    print(f'- Using Alexa Event Gateway \"{event_gateway}\"')
    read_creds()

    if access_token == '' or refresh_token == '':
        print('- One or more access tokens missing in credentials file')
        
        if not request_access_tokens():
            sys.exit(-1)
    else:
        print('- Access tokens found in credentials file')
    if len(sys.argv) > 1 and sys.argv[1] == 'press':
        trigger_doorbell()
    