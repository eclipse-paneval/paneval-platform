# PanEval\-API Interface Requirements

# Background

Currently, the PanEval evaluation platform requires the construction of evaluation interfaces that adhere to the platform's interface standards to standardize evaluation criteria\. The provided evaluation interfaces must support standard APIs and be invoked via HTTP POST requests\.

To specify the concurrency level supported by the interface, the "workers" parameter should be appended to the request URL\. For example:https://api\.panda\-v\.com/v1?workers=4



# LLM Requirements

## request Interface：

Authentication: If authentication is required, a long\-term valid OPENAI\_API\_KEY can be provided for authentication\.

Header: Must support JSON format data\.

```Bash
"Content-Type": "application/json" 
```

**body:**

|parameterName|type|description|required|
|---|---|---|---|
|model|string|Model Selection Parameter|true|
|messages|MessageInfo\[\]|Data for the Large Model|true|
|temperature|float|Randomness parameter|false|
|max\_token|int|Generated text length|false|
|\.\.\.||||





MessageInfo Data:

|parameterName|type|description|required|
|---|---|---|---|
|role|string|role name|true|
|content|string|content|true|
|\.\.\.||||

request example：

```Bash
headers={
    "Content-Type": "application/json"，
    "Authorization": "Bearer $OPENAI_API_KEY"
    }
data={
     "model": "gpt-4o-mini",
     "messages": [{"role": "user", "content": "Say this is a test!"}],
     "temperature": 0.7
   }
response = requests.post(url, headers=headers, data=json.dumps(data))
```

## response data:

The output of the model must be in the `choices` field\.

|parameterName|type|description|required|
|---|---|---|---|
|err\_code|int|0 for success, 1 for failure|true|
|err\_message|string|Request processing message|true|
|id|string|Unique identifier|true|
|choices|ChoiceInfo\[\]|Model output|true|
|\.\.\.||||







ChoiceInfo Data：

|parameterName|type|description|required|
|---|---|---|---|
|message|MessageInfo\[\]|Model output|true|
|\.\.\.||||

MessageInfo Data：

|parameterName|type|description|required|
|---|---|---|---|
|role|string|role name|true|
|content|string|content|true|
|\.\.\.||||

Response example：

```JSON
{
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "created": 1677858242,
    "model": "gpt-4o-mini",
    "usage": {
        "prompt_tokens": 13,
        "completion_tokens": 7,
        "total_tokens": 20,
        "completion_tokens_details": {
            "reasoning_tokens": 0,
            "accepted_prediction_tokens": 0,
            "rejected_prediction_tokens": 0
        }
    },
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "\n\nThis is a test!"
            },
            "logprobs": null,
            "finish_reason": "stop",
            "index": 0
        }
    ]
}
```

# VLM Requirements

## request Interface：

**Authentication**: If authentication is required, a long\-lasting API key can be provided for authentication\.

**Header**: The request should support JSON format data\.

```Bash
"Content-Type: application/json" 
```

**body:**

|parameterName|type|description|required|
|---|---|---|---|
|model|string|Model Selection Parameter|true|
|messages|MessageInfos\[\]|Data for the Large Model|true|
|temperature|float|Randomness parameter|false|
|max\_token|int|Generated text length|false|
|\.\.\.||||

MessageInfos Data

|parameterName|type|description|required|
|---|---|---|---|
|role|string|role name|true|
|content|ContentInfo\[\]|content|true|
|\.\.\.||||







ContenInfo Data

|parameterName|type|description|required|
|---|---|---|---|
|type|string|Field Type: The type of the field, such as `text` or `image_url`|true|
|text|string|User Input Information|false|
|image\_url|string|User Input Image in Base64|false|

**Request example**

```Bash
curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-4o",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "What'\''s in this image?"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": f"data:image/jpeg;base64,{base64_image}",
            }
          }
        ]
      }
    ],
    "max_tokens": 300
  }'

```

## response data:

The model's output must be in the `choices` field\. If this field is not available, the request is considered a failure\.

|parameterName|type|description|required|
|---|---|---|---|
|err\_code|int|0 for success, 1 for failure|true|
|err\_message|string|Request processing message|true|
|id|string|Unique identifier|true|
|choices|ChoiceInfo\[\]|Model output|true|
|\.\.\.||||

ChoiceInfo Data

|parameterName|type|description|required|
|---|---|---|---|
|message|MessageInfo\[\]|Model output|true|
|\.\.\.||||

MessageInfo Data

|parameterName|type|description|required|
|---|---|---|---|
|role|string|role name|true|
|content|string|content|true|
|\.\.\.||||

Response example

```Bash
{
  "id":"",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "\n\nThis image shows a wooden boardwalk extending through a lush green marshland.",
    }]
}
```





