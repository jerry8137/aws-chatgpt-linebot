# 20230316 AWS ChatGPT LineBot

###### tags: `AWS Learning Group`

## Overview

延續Kevin 的[GPT3 Linebot](https://hackmd.io/@_ZfaCsoORM2ms6z9wV-aNw/HJmrePJOs) 加上用DynamoDB 儲存conversation 的功能，以及換上新推出的ChatGPT API~

## Prerequisite

1. AWS CLI
2. npm
3. conda
4. OpenAI API account with payment set (or still in free trial)
5. [LineBot](https://developers.line.biz/en/)

Prepair your:
```=
OpenAI API key
Linebot: Channel_access_token and Channel_secret
AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
```

## OpenAI API

We are using ChatCompletion model (gpt-3.5-turbo), which is the same model behind ChatGPT.
See [Documentation](https://platform.openai.com/docs/guides/chat)

### Usage

Ex:
```pytohn=
# Note: you need to be using OpenAI Python v0.27.0 for the code below to work
import openai

openai.ChatCompletion.create(
  model="gpt-3.5-turbo",
  messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who won the world series in 2020?"},
        {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
        {"role": "user", "content": "Where was it played?"}
    ]
)
```

There are no session managed by the api now.
We can maintain session by storing the conversation and feed it to the model again and again.

Ex:
```python=
import openai

openai.api_key = "XXXX" # supply your API key however you choose

message = {"role":"user", "content": input("This is the beginning of your chat with AI. [To exit, send \"###\".]\n\nYou:")};

conversation = [{"role": "system", "content": "DIRECTIVE_FOR_gpt-3.5-turbo"}]

while(message["content"]!="###"):
    conversation.append(message)
    completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=conversation) 
    message["content"] = input(f"Assistant: {completion.choices[0].message.content} \nYou:")
    print()
    conversation.append(completion.choices[0].message)
```

### Pricing

**gpt-3.5-turbo**: $0.002 / 1K tokens

## Use Serverless to Deploy Lambda & DynamoDB

### Prepare conda env

```lua=
conda create -n chatgpt_linebot python=3.9
conda activate chatgpt_linebot
pip install line-bot-sdk==1.12.1 openai boto3
```

### Prepare Serverless framework

```lua=
export AWS_ACCESS_KEY_ID=**********
export AWS_SECRET_ACCESS_KEY=***********
npm install serverless -g
serverless create --template aws-python --path aws-line-ChatGPT-bot
```

### Change the keys in `serverless.yml`

Paste your `Channel_accesss_token`, `Channel_secret`, `openAI_API_token` in `serverless.yml`: `provider.environment`

### Deploy!!!

```lua=
sls deploy
```
maybe need to use `sudo`, I'm not sure how to fix


### Set the permission for Lambda to access DynamoDB

DynamoDB -> Tables -> chatgpt-conversation-table
overview -> additional info
copy the **Amazon Resource Name (ARN)**

uncomment these lines and paster your ARN:
```yaml=
  iam:
    role:
      statements:
        - Effect: Allow
          Action:
            - dynamodb:*
          Resource:
            - "YOUR_ARN"
```

## Done!!!

Try it out.
Use CloudWatch to check logs and debug if needed.

Logs are automatically stored in S3.