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

import boto3
import json
from alexa.skills.smarthome import AlexaResponse
from botocore.config import Config

boto3.client('dynamodb', config=Config(region_name = 'eu-west-1'))
aws_dynamodb = boto3.client('dynamodb')

def lambda_handler(request, context):
    print('- lambda_handler(...), request:')
    print(json.dumps(request), indent = 2)

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
                supported = [{'name': 'powerState'}]
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
                capabilities = [capability_alexa, capability_powercontroller]
            )

            return send_response(response_discovery.get())

    if namespace == 'Alexa.PowerController':
        endpoint_id = request['directive']['endpoint']['endpointId']
        power_state_value = 'OFF' if name == 'TurnOff' else 'ON'
        correlation_token = request['directive']['header']['correlationToken']

        state_set = set_device_state(endpoint_id=endpoint_id, state='powerState', value=power_state_value)
        if not state_set:
            return send_error_response('ENDPOINT_UNREACHABLE', 'Error while trying to set endpoint state in the database')

        apcr = AlexaResponse(correlation_token=correlation_token)
        apcr.add_context_property(namespace = 'Alexa.PowerController', name = 'powerState', value = power_state_value)
        return send_response(apcr.get())

def send_error_response(type, message):
    return send_response(
        AlexaResponse(
            name = 'ErrorResponse',
            payload = { 'type': type, 'message': message }
        ).get()
    )

def send_response(response):
    # TODO Validate the response
    print('lambda_handler response -----')
    print(json.dumps(response))
    return response


def set_device_state(endpoint_id, state, value):
    attribute_key = state + 'Value'
    response = aws_dynamodb.update_item(
        TableName = 'SampleSmartHome',
        Key={'ItemId': {'S': endpoint_id}},
        AttributeUpdates={attribute_key: {'Action': 'PUT', 'Value': {'S': value}}})
    print(response)
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return True
    else:
        return False
