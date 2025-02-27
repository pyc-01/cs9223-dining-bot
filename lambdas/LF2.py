import json
import os
import boto3

# --- SQS Helper Functions ---
def fetch_request():
    """Fetch a request from SQS queue"""
    print("SQS RUNNING")
    sqs = boto3.client('sqs')
    QUEUE_URL = os.environ['QUEUE_URL']

    print("FETCHING A REQUEST")
    messages = sqs.receive_message(
        QueueUrl=QUEUE_URL, 
        MaxNumberOfMessages=1,
        WaitTimeSeconds=20,
        MessageAttributeNames=['All']
    )
    if 'Messages' in messages:
        request = messages['Messages'][0]
        print("FETCHED A REQUEST")
        return request
    else:
        print("NO REQUESTS FOUND")
        return None

def delete_request(receipt_handle):
    """Delete a request from SQS queue"""
    print("SQS RUNNING")
    sqs = boto3.client('sqs')
    QUEUE_URL = os.environ['QUEUE_URL']

    print("DELETING A REQUEST")
    try:
        sqs.delete_message(
            QueueUrl=QUEUE_URL,
            ReceiptHandle=receipt_handle
        )
        print("REQUEST DELETED")
    except Exception as e:
        print(f"SQS ERROR: {e}")

# --- SES Helper Functions ---
def send_email(request_attributes):
    """Send email through SES"""
    print("SES RUNNING")
    ses = boto3.client('ses')
    SENDER_EMAIL = os.environ['SENDER_EMAIL']

    receiver_email = request_attributes['Email']['StringValue']
    cuisine = request_attributes['Cuisine']['StringValue']

    print("SENDING AN EMAIL")
    try:
        ses.send_email(
            Source=SENDER_EMAIL,
            Destination={
                'ToAddresses': [receiver_email]
            },
            Message={
                'Subject': {
                    'Data': f"LF2: (PLACEHOLDER) {cuisine} Cuisine Suggestions"
                },
                'Body': {
                    'Text': {
                        'Data': f"(PLACEHOLDER) Hello! Here are my {cuisine} cuisine suggestions. \n {request_attributes}"
                    }
                }
            }
        )
        print("EMAIL SENT")
    except Exception as e:
        print(f"SES ERROR: {e}")

# --- Main Lambda Handler ---
def lambda_handler(event, context):
    # TODO implement
    print("NOW CALLING SQS")
    request = fetch_request()
    print("SQS FINISHED")

    if request is not None:
        receipt_handle = request['ReceiptHandle']
        request_attributes = request['MessageAttributes']

        print("NOW CALLING SES")
        send_email(request_attributes)
        print("SES FINISHED")

        print("NOW CALLING SQS")
        delete_request(receipt_handle)
        print("SQS FINISHED")

        return(request)
    else:
        return {
            'statusCode': 404,
            'body': json.dumps('No requests found')
        }


