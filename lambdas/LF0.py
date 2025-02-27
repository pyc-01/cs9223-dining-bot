import json
import os
import boto3

# --- Lex Integration ---
def lex_handler(message):
    """Lex function for API"""
    try:
        print("LEX RUNNING")
        lex_client = boto3.client('lexv2-runtime')

        BOT_ID = os.environ['BOT_ID']
        BOT_ALIAS_ID = os.environ['BOT_ALIAS_ID']
        LOCALE_ID = 'en_US'

        response = lex_client.recognize_text(
            botId=BOT_ID,
            botAliasId=BOT_ALIAS_ID,
            localeId=LOCALE_ID,
            sessionId='test',
            text=message
        )
        print(f"LEX_RESPONSE: {response}")
        return response
    except Exception as e:
        print(f"LEX_ERROR: {e}")
        return "Sorry, it seems something went wrong."

# --- Main Lambda Handler ---
def lambda_handler(event, context):
    # TODO implement
    message = event['messages'][0]['unstructured']['text']

    print("NOW CALLING LEX")
    lex_response = lex_handler(message)
    lex_message = lex_response['messages'][0]['content']
    print(f"LEX_MESSAGE: {lex_message}")
    print("LEX FINISHED")

    response = {
        'messages': [
            {
                'type': 'unstructured',
                'unstructured': {
                    'text': lex_message
                }
            }
        ]
    }

    return response