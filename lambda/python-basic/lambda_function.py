# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Amazon Software License (the "License"). You may not use this file except in
# compliance with the License. A copy of the License is located at
#
#   http://aws.amazon.com/asl/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific
# language governing permissions and limitations under the License.

# ---
# This source file has been modified. It's original version can be found in the following repository:
#   https://github.com/alexa-samples/skill-sample-python-smarthome-switch
# ---

import boto3
import json
from botocore.config import Config

from alexa.skills.smarthome import AlexaResponse

ALEXA_REGION = 'eu-west-1'
DYNAMODB_TABLE_NAME = 'smart-home-states'

boto3.client('dynamodb', config=Config(region_name = ALEXA_REGION))
aws_dynamodb = boto3.client('dynamodb')

def lambda_handler(request, context):
    print('- lambda_handler(...), request:')
    print(json.dumps(request))

    print('- lambda_handler(...), context:')
    print(context)

    if 'directive' not in request:
        return send_error_response('INVALID_DIRECTIVE', 'Invalid Alexa Directive: key \'directive\' missing')

    if request['directive']['header']['payloadVersion'] != '3':
        return send_error_response('INTERNAL_ERROR', 'Incorrect API version: only Smart Home API v3 supported')

    name = request['directive']['header']['name']
    namespace = request['directive']['header']['namespace']

    if namespace == 'Alexa.Authorization':
        if name == 'AcceptGrant':
            return send_response(
                AlexaResponse(
                    namespace = 'Alexa.Authorization',
                    name = 'AcceptGrant.Response'
                ).get()
            )

    if namespace == 'Alexa.Discovery':
        if name == 'Discover':
            response_discovery = AlexaResponse(namespace = 'Alexa.Discovery', name = 'Discover.Response')
            capability_alexa = response_discovery.create_payload_endpoint_capability()
            
            capability_doorbell = response_discovery.create_payload_endpoint_capability(
                interface = 'Alexa.DoorbellEventSource',
                proactively_reported = True
            )

            capability_powercontroller = response_discovery.create_payload_endpoint_capability(
                interface = 'Alexa.PowerController',
                supported = [{'name': 'powerState'}],
                proactively_reported = True,
                retrievable = True
            )

            response_discovery.add_payload_endpoint(
                friendly_name = 'Sample Doorbell',
                endpoint_id = 'sample-doorbell-001',
                display_categories = ["DOORBELL"],
                capabilities = [capability_alexa, capability_doorbell]
            )

            response_discovery.add_payload_endpoint(
                friendly_name = 'Sample Switch',
                endpoint_id = 'sample-switch-001',
                display_categories = ["SWITCH"],
                capabilities = [capability_alexa, capability_powercontroller]
            )

            return send_response(response_discovery.get())

    if namespace == 'Alexa.PowerController':
        endpoint_id = request['directive']['endpoint']['endpointId']
        power_state_value = 'OFF' if name == 'TurnOff' else 'ON'
        correlation_token = request['directive']['header']['correlationToken']

        state_set = set_device_state(endpoint_id = endpoint_id, state = 'powerState', value = power_state_value, use_dynamodb = True)
        if not state_set:
            return send_error_response('ENDPOINT_UNREACHABLE', 'Error while trying to set endpoint state in the database')

        response_powercontroller = AlexaResponse(correlation_token = correlation_token)
        response_powercontroller.add_context_property(namespace = 'Alexa.PowerController', name = 'powerState', value = power_state_value)
        return send_response(response_powercontroller.get())

    if namespace == 'Alexa' and name == 'ReportState':
        endpoint_id = request['directive']['endpoint']['endpointId']
        correlation_token = request['directive']['header']['correlationToken']
        
        state = get_device_state(endpoint_id = endpoint_id, use_dynamodb = True)
        
        response_statereport = AlexaResponse(correlation_token = correlation_token, namespace = 'Alexa', name = 'StateReport', endpoint_id = endpoint_id, cookie = {})
        response_statereport.add_context_property(namespace = 'Alexa.PowerController', name = 'powerState', value = state)
        return send_response(response_statereport.get())

def send_error_response(type, message):
    return send_response(
        AlexaResponse(
            name = 'ErrorResponse',
            payload = { 'type': type, 'message': message }
        ).get()
    )

def send_response(response):
    print('- send_response(...), response:')
    print(json.dumps(response))
    return response

def get_device_state(endpoint_id, use_dynamodb = True):
    if use_dynamodb:
            response = aws_dynamodb.get_item(
                TableName = DYNAMODB_TABLE_NAME,
                Key = {
                    'item.id': { 'S': endpoint_id }
                }
            )

            return response['Item']['item.state']['M']['powerStateValue']['S']


def set_device_state(endpoint_id, state, value, use_dynamodb = True):
    if use_dynamodb:
        response = aws_dynamodb.update_item(
            TableName = DYNAMODB_TABLE_NAME,
            Key = {
                'item.id': { 'S': endpoint_id }
            },
            AttributeUpdates = {
                'item.state': {
                    'Action': 'PUT',
                    'Value': {
                        'M': {
                            state + 'Value': {
                                'S': value
                            }
                        }
                    }
                }
            }
        )

        print('- set_device_state(...), response:')
        print(response)

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return True
        else:
            return False

    else:
        return False