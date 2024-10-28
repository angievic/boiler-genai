from typing import Dict, Any, List
import json
import boto3

MAX_TOKENS_PER_PROMPT = 40000

# Initialize the Bedrock client
bedrock = boto3.client('bedrock-runtime')

def call_llm(prompt: str, max_tokens: int = 40000, temperature: float = 0.9) -> List[Dict[str, Any]]:
    """
    Generate text using the Claude 3 Haiku model via Amazon Bedrock.
    
    :param prompt: The input text to generate a continuation for.
    :param max_tokens: The maximum number of tokens to generate.
    :param temperature: Controls randomness in generation. Higher values make output more random.
    :return: A text response.
    """
    # Prepare the request body for Claude 3 Haiku
    request_body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "user",
                "content": f"{prompt}"
            }
        ],
        "temperature": temperature
    })
    # Call the Bedrock API with Claude 3 Haiku model
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-haiku-20240307-v1:0',  # Use the appropriate model ID for Claude
        body=request_body
    )

    # Parse the response
    response_body = json.loads(response['body'].read())
    return response_body['content'][0]['text']

def call_llm_with_history_messages(prompt: str, messages: List[dict], max_tokens: int = 40000, temperature: float = 0.9) -> List[Dict[str, Any]]:
    """
    Generate text using the Claude 3 Haiku model via Amazon Bedrock.
    
    :param prompt: The input text to generate a continuation for.
    :param max_tokens: The maximum number of tokens to generate.
    :param temperature: Controls randomness in generation. Higher values make output more random.
    :return: A text response.
    """
    # Prepare the request body for Claude 3 Haiku
    request_body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "user",
                "content": f"{prompt}"
            }
        ] + messages ,
        "temperature": temperature
    })
    # Call the Bedrock API with Claude 3 Haiku model
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-haiku-20240307-v1:0',  # Use the appropriate model ID for Claude
        body=request_body
    )

    # Parse the response
    response_body = json.loads(response['body'].read())
    return response_body['content'][0]['text']
