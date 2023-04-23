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

import time
import json
import threading
from queue import Queue, Empty as EmptyException
from flask import Flask, render_template, request, jsonify

import boto3
from boto3 import dynamodb
from boto3.dynamodb.conditions import Key, Attr

remote_switch_state_queue = Queue(maxsize = 1)
local_switch_state_queue = Queue(maxsize = 1)
doorbell_event = threading.Event()

app = Flask(__name__, template_folder = '.')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/remote_switch_change', methods=['GET'])
def remote_switch_change():
    return_status = 'no-change'
    remote_switch_state = ''
    try:
        remote_switch_state = remote_switch_state_queue.get(block = False)
        return_status = 'new-value'
    except EmptyException:
        pass
    return jsonify({'status': return_status, 'value': remote_switch_state})

@app.route('/physical_switch_change', methods=['POST'])
def physical_switch_change():
    checkbox_state = request.get_json()
    local_switch_state_queue.put(checkbox_state)
    return json.dumps({'success': True})

@app.route('/doorbell_pressed', methods=['POST'])
def doorbell_pressed():
    global doorbell_event

    doorbell_event.set()
    return json.dumps({'success': True})

def start(doorbell_trigger_callback, switch_change_report_callback):
    threading.Thread(target = lambda: app.run(debug = True, use_reloader = False), daemon = True).start()

    session = boto3.Session(profile_name = 'dev')
    dynamodb_client = session.client('dynamodb')

    prev_remote_switch_state = ''
    while True:
        time.sleep(1)
        response = dynamodb_client.get_item(TableName = 'smart-home-states', Key = {'item.id': {'S': 'sample-switch-001'}})
        new_remote_switch_state = response['Item']['item.state']['M']['powerStateValue']['S']

        if new_remote_switch_state != prev_remote_switch_state:
            prev_remote_switch_state = new_remote_switch_state
            print(f'Sample Switch: {new_remote_switch_state}')
            remote_switch_state_queue.put(new_remote_switch_state)
        
        if doorbell_event.is_set():
            doorbell_event.clear()
            print("doorbell_pressed")
            doorbell_trigger_callback()

        try:
            local_switch_state = local_switch_state_queue.get(block = False)
            print(f'switch: {local_switch_state}')
        except EmptyException:
            pass
