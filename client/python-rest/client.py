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

from constants import *
import auth
import webapp

def switch_change_report():
    pass

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
                    'token': auth.access_token,
                },
                'endpointId': DOORBELL_ENDPOINT_ID,
            },
            'payload': {
                'cause': {
                    'type': 'PHYSICAL_INTERACTION',
                },
                'timestamp': auth.get_timestamp(),
            },
        },
    }

    print('- Sending doorbell event.......', end = '')

    response = requests.post(
        EVENT_GATEWAY + '?Authorization=Bearer ' + auth.access_token,
        headers = headers,
        json=json_data,
    )

    if response.status_code != HTTP_RESPONSE_ACCEPTED:
        response_json = response.json()
        print(response_json['payload']['code'] + '!')

        if response_json['payload']['code'] == 'INVALID_ACCESS_TOKEN_EXCEPTION':
            auth.refresh_access_tokens()
        else:
            print(json.dumps(response_json, indent = 2))
    else:
        print('OK!')

if __name__ == '__main__':
    print(f'- Using Alexa Event Gateway \"{EVENT_GATEWAY}\"')
    auth.read_credentials()

    if auth.access_token == '' or auth.refresh_token == '':
        print('- One or more access tokens missing in credentials file')
        
        if not auth.request_access_tokens():
            sys.exit(-1)
    else:
        print('- Access tokens found in credentials file')

    webapp.start(trigger_doorbell, switch_change_report)
