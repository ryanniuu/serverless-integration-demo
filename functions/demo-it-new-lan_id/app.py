import json
import random

def lambda_handler(event, context):
    # TODO implement
    return {
        "statusCode": 200,
        "first_name": event['first_name'],
        "last_name": event['last_name'],
        "personal_email": event['personal_email'],
        "lan_id": event['first_name']+'.'+event['last_name']
    }
