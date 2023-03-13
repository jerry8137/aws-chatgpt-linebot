import os
import json
import openai
import boto3

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
'''
Setting LINE
'''
line_bot_api = LineBotApi(os.environ['Channel_access_token'])
handler = WebhookHandler(os.environ['Channel_secret'])

'''
Setting OpenAI
'''
openai.api_key = os.environ['openAI_API_token']

dynamodb = boto3.resource('dynamodb')
table_name = 'chat-conversation-table'
table = dynamodb.Table(table_name)


def resetSession(conversation):
    items = conversation['Items']
    with table.batch_writer() as batch:
        for item in items:
            key = {'user_id': item['user_id']}
            if 'timestamp' in item:
                key['timestamp'] = item['timestamp']
            batch.delete_item(Key=key)


def webhook(event, context):
    # Parse msg from LINE conversation request
    print('event: ', event)
    msg = json.loads(event['body'])
    print('msg: ', msg)

    # Parse texts we type from msg
    user_id = msg['events'][0]['source']['userId']
    user_input = msg['events'][0]['message']['text']
    print('user_id: ', user_id)
    print('user_input:', user_input)

    # Get the conversation data from DynamoDB
    conversation = table.query(
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={
                ':uid': user_id
                }
            )
    # check if the conversation data exists
    if len(conversation['Items']) != 0:
        print('conversation: ', conversation['Items'][0]['conversation'])

    if user_input == 'reset':
        resetSession(conversation)
        try:
            line_bot_api.reply_message(
                    msg['events'][0]['replyToken'],
                    TextSendMessage(text='Conversation history has been deleted. Please start a new conversation.')
            )
        except:
            return {
                'statusCode': 502,
                'body': json.dumps("Invalid signature. Please check your channel access token/channel secret.")
            }
        return {
            "statusCode": 200,
            "body": json.dumps({"message": 'ok'})
        }

    prompt = [
            {"role": "system", "content": "You are a helpful and kind AI Assistant."},
            ]
    if len(conversation['Items']) != 0:
        prompt = prompt + conversation['Items'][0]['conversation']
    prompt.append({"role": "user", "content": user_input})
    print('prompt: ', prompt)
    # GPT3
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=prompt
    )
    gpt3_response = response.choices[0]['message']['content']
    print('gpt3_response: ', gpt3_response)

    # Store the conversation data in DynamoDB
    table.update_item(
        Key={'user_id': user_id},
        UpdateExpression='SET conversation = list_append(if_not_exists(conversation, :empty_list), :conversation)',
        ExpressionAttributeValues={
            ':conversation': [{'role': 'user', 'content': user_input}, {'role': 'system', 'content': gpt3_response}],
            ':empty_list': []
            }
        )

    # handle webhook body
    try:
        line_bot_api.reply_message(
                msg['events'][0]['replyToken'],
                TextSendMessage(text=gpt3_response)
        )
    except:
        return {
            'statusCode': 502,
            'body': json.dumps("Invalid signature. Please check your channel access token/channel secret.")
        }
    return {
        "statusCode": 200,
        "body": json.dumps({"message": 'ok'})
    }
