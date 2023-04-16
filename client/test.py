import time
import boto3
from boto3 import dynamodb
from boto3.dynamodb.conditions import Key, Attr

session = boto3.Session(profile_name='dev')
dynamodb_client = session.client('dynamodb')

prev_state = ''
while True:
    time.sleep(1)
    response = dynamodb_client.get_item(TableName = 'smart-home-states', Key = {'item.id': {'S': 'sample-switch-001'}})
    new_state = response['Item']['item.state']['M']['powerStateValue']['S']

    if new_state != prev_state:
        prev_state = new_state
        print(f'Sample Switch: {new_state}')

