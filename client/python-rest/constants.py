HTTP_RESPONSE_OK = 200
HTTP_RESPONSE_ACCEPTED = 202

ALEXA_REGION = 'eu-west-1'

DOORBELL_ENDPOINT_ID = 'sample-doorbell-001'

CREDENTIALS_PATH = "..\\..\\.credentials"

LWA_TOKEN_URI = 'https://api.amazon.com:443/auth/o2/token'

EVENT_GATEWAY_DICT = {
    'eu-west-1': 'https://api.eu.amazonalexa.com/v3/events',
    'us-east-1': 'https://api.amazonalexa.com/v3/events',
    'us-west-2': 'https://api.fe.amazonalexa.com/v3/events',
}

EVENT_GATEWAY = EVENT_GATEWAY_DICT[ALEXA_REGION]
