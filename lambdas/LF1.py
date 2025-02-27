import json
import os
import datetime
import time
import re
import boto3

# --- Helper Functions ---
def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """Elicit a slot"""
    return {
        "sessionState": {
            "sessionAttributes": session_attributes,
            "dialogAction": {
                "type": "ElicitSlot",
                "slotToElicit": slot_to_elicit
            },
            "intent": {
                "name": intent_name,
                "slots": slots,
            },
        },
        "messages": [
            {
                "contentType": "PlainText", 
                "content": message
            }
        ]
    }

def close(session_attributes, intent_name, slots, fulfillment_state, message):
    """Close the session"""
    return {
        "sessionState": {   
            "sessionAttributes": session_attributes,
            "dialogAction": {
                "type": "Close",
            },
            "intent": {
                "name": intent_name,
                "slots": slots,
                "state": fulfillment_state
            }
        },
        "messages": [
            {
                "contentType": "PlainText", 
                "content": message
            }
        ]
    }

def delegate(session_attributes, intent_name, slots):
    """Delegate to Lex"""
    return {
        "sessionState": {
            "sessionAttributes": session_attributes,
            "dialogAction": {
                "type": "Delegate",
            },
            "intent": {
                "name": intent_name,
                "slots": slots
            }
        }
    }

def build_validation_result(is_valid, invalid_slot, message_content):
    """Build validation result"""
    return {
        "isValid": is_valid,
        "invalidSlot": invalid_slot,
        "message": message_content
    }

def send_to_sqs(slots):
    """Send slot results to SQS"""
    print("SQS RUNNING")
    sqs = boto3.client('sqs')
    QUEUE_URL = os.environ['QUEUE_URL']

    try:
        print("SQS SENDING A MESSAGE")
        response = sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody="Slot information",
            MessageAttributes={
                'Location': {
                    'DataType': 'String',
                    'StringValue': slots['Location']["value"]["interpretedValue"]
                },
                'Cuisine': {
                    'DataType': 'String',
                    'StringValue': slots['Cuisine']["value"]["interpretedValue"]
                },
                'DiningDate': {
                    'DataType': 'String',
                    'StringValue': slots['DiningDate']["value"]["interpretedValue"]
                },
                'DiningTime': {
                    'DataType': 'String',
                    'StringValue': slots['DiningTime']["value"]["interpretedValue"]
                },
                'PartySize': {
                    'DataType': 'Number',
                    'StringValue': slots['PartySize']["value"]["interpretedValue"]
                },
                'Email': {
                    'DataType': 'String',
                    'StringValue': slots['Email']["value"]["interpretedValue"]
                }
            }
        )
        print(f"SQS_RESPONSE: {response}")
        return response
    except Exception as e:
        print(f"SQS ERROR: {e}")

# --- Slot Validation Functions ---
def is_valid_location(location):
    """Validate location"""
    valid_locations = ["manhattan"]
    return location["value"]["interpretedValue"].lower() in valid_locations

def is_valid_cuisine(cuisine):
    """Validate cuisine"""
    valid_cuisines = ["chinese", "italian", "mexican"]
    return cuisine["value"]["interpretedValue"].lower() in valid_cuisines

def is_valid_date(date):
    """Validate date"""
    if datetime.datetime.strptime(date["value"]["interpretedValue"], "%Y-%m-%d").date() < datetime.date.today():
        return False
    return True

def is_valid_time(date, time):
    """Validate time"""
    if datetime.datetime.strptime(date["value"]["interpretedValue"], "%Y-%m-%d").date() == datetime.date.today():
        if datetime.datetime.strptime(time["value"]["interpretedValue"], "%H:%M").time() <= datetime.datetime.now().time():
            return False
    return True

def is_valid_party_size(party_size):
    """Validate party size"""
    return int(party_size["value"]["interpretedValue"]) > 0 and int(party_size["value"]["interpretedValue"]) <= 20

def is_valid_email(email):
    """Validate email"""
    return re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email["value"]["interpretedValue"]) is not None

def validate_request(location, cuisine, date, time, party_size, email):
    """Validate request"""
    if location is not None and not is_valid_location(location):
        return build_validation_result(False, "Location", f"Sorry, {location["value"]["interpretedValue"]} is not supported yet. Please try another location.")

    if cuisine is not None and not is_valid_cuisine(cuisine):
        return build_validation_result(False, "Cuisine", f"Sorry, {cuisine["value"]["interpretedValue"]} is not supported yet. Please try another cuisine.")

    if date is not None and not is_valid_date(date):
        return build_validation_result(False, "DiningDate", "The date entered is not valid. Please enter a valid date.")

    if time is not None and not is_valid_time(date, time):
        return build_validation_result(False, "DiningTime", "The time entered is not valid. Please enter a valid time.")

    if party_size is not None and not is_valid_party_size(party_size):
        return build_validation_result(False, "PartySize", "Please enter a party size between 1 and 20.")

    if email is not None and not is_valid_email(email):
        return build_validation_result(False, "Email", "Please enter a valid email address.")

    return build_validation_result(True, None, None)

# --- Intent Handlers ---
def greeting(event):
    """Handle GreetingIntent"""
    return {
        "sessionState": {
            "dialogAction": {
                "type": "ElicitIntent",
            }
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": "Hi there, how can I help?"
            }
        ]
    }

def thank_you(event):
    """Handle ThankYouIntent"""
    return {
        "sessionState": {
            "dialogAction": {
                "type": "ElicitIntent",
            }
        },
        "messages": [
                {
                    "contentType": "PlainText",
                    "content": "You are welcome!"
                }
        ]
    }

def dining_suggestions(event):
    """Handle DiningSuggestionsIntent"""
    session_attributes = event["sessionState"]["sessionAttributes"] if event["sessionState"]["sessionAttributes"] is not None else {}
    intent_name = event["interpretations"][0]["intent"]["name"]
    slots = event["interpretations"][0]["intent"]["slots"]
    
    # Extract slot values
    location = slots["Location"]
    cuisine = slots["Cuisine"]
    date = slots["DiningDate"]
    time = slots["DiningTime"]
    party_size = slots["PartySize"]
    email = slots["Email"]

    # Validate slot values
    validation_result = validate_request(location, cuisine, date, time, party_size, email)
    if not validation_result["isValid"]:
        return elicit_slot(session_attributes,
                           intent_name,
                           slots,
                           validation_result["invalidSlot"],
                           validation_result["message"])

    print(f"VALIDATION_RESULT: {validation_result}")

    # If called in DialogCodeHook, delegate control back to Lex
    if event["invocationSource"] == "DialogCodeHook":
        print("DELEGATING BACK TO BOT")
        return delegate(session_attributes, intent_name, slots)

    # Send request to SQS
    print("NOW CALLING SQS")
    send_to_sqs(slots)
    print("SQS FINISHED")

    # Fulfillment message
    print("FULFILLING REQUEST")
    message = "Great! Your request has been received. Recommendations will be sent to the email provided."
    return close(session_attributes, intent_name, slots, "Fulfilled", message)
    
# --- Intent Dispatcher ---
def dispatch(event):
    """Route to respective intent handler"""
    print(f"EVENT_RECEIVED: {event}")

    intent_name = event["interpretations"][0]["intent"]["name"]

    if intent_name == "GreetingIntent":
        print("GREETING_INTENT DETECTED")
        return greeting(event)

    if intent_name == "DiningSuggestionsIntent":
        print("DINING_SUGGESTIONS_INTENT DETECTED")
        return dining_suggestions(event)

    if intent_name == "ThankYouIntent":
        print("THANK_YOU_INTENT DETECTED")
        return thank_you(event)

    raise Exception(f"Intent with name {intent_name} not supported")
    
# --- Main Lambda Handler ---
def lambda_handler(event, context):
    """Main handler for incoming requests"""
    os.environ["TZ"] = "America/New_York"
    time.tzset()
    return dispatch(event)
