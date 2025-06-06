from typing import Dict, Any, List, Optional
import json
import boto3
from botocore.config import Config

# Configure the Bedrock client with a custom timeout
bedrock_config = Config(
    read_timeout=120,  # Increase the read timeout to 120 seconds
    connect_timeout=10  # Increase the connect timeout if needed
)
# Runtime for call models
bedrock = boto3.client('bedrock-runtime',config=bedrock_config)

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

def call_llm_analyze_images(prompt: str, images: Optional[List[str]], max_tokens: int = 8192, temperature: float = 0) -> List[Dict[str, Any]]:
    """
    Generate text using Llama Vision model via Amazon Bedrock.
    """
    # Prepare the request body for Llama Vision model
    request_body = json.dumps({
        "prompt": prompt,
        "images": images,
        "temperature": temperature,
        "max_gen_len": max_tokens,
        "images": images
    })
    
    model_id = "us.meta.llama3-2-11b-instruct-v1:0"
    response = bedrock.invoke_model(
        modelId=model_id,
        body=request_body,
        contentType="application/json",
        accept="application/json"
    )
    response_body = json.loads(response['body'].read())
    return response_body

def call_llm_to_generate_image(
    prompt: str, 
    cfg_scale: float = 8,
    height: int = 720,
    width: int = 1280,
    seed: int = 42,
    quality: str = "standard",
    number_of_images: int = 1
) -> List[Dict[str, Any]]:
    """
    Generate images using Amazon's Nova Canvas model via Bedrock.
    
    :param prompt: The text description of the image to generate
    :param cfg_scale: Controls how closely the image matches the prompt (default: 8)
    :param height: Image height in pixels (default: 720)
    :param width: Image width in pixels (default: 1280)
    :param seed: Random seed for reproducible results (default: 42)
    :param quality: Image quality setting (default: "standard")
    :param number_of_images: Number of images to generate (default: 1)
    :return: Base64 encoded image data
    """
    request_body = {
        "textToImageParams": {
            "text": prompt
        },
        "taskType": "TEXT_IMAGE",
        "imageGenerationConfig": {
            "cfgScale": cfg_scale,
            "seed": seed,
            "quality": quality,
            "width": width,
            "height": height,
            "numberOfImages": number_of_images
        }
    }
    
    model_id = "amazon.nova-canvas-v1:0"
    response = bedrock.invoke_model(
        modelId=model_id,
        body=json.dumps(request_body),
        contentType="application/json",
        accept="application/json"
    )
    response_body = json.loads(response['body'].read())
    return response_body["images"][0]

def call_llm_using_trained_model(prompt: str, max_tokens: int = 4096, temperature: float = 0.9, model_id: str = "cohere.command-light-text-v14") -> List[Dict[str, Any]]:
    """
    Generate text using the Cohere model via Amazon Bedrock.
    
    :param prompt: The input text to generate a continuation for.
    :param max_tokens: The maximum number of tokens to generate.
    :param temperature: Controls randomness in generation. Higher values make output more random.
    :return: A text response.
    """
    # Prepare the request body for Cohere model
    response = bedrock.invoke_model(
        modelId=model_id,  # Updated model ID
        contentType="application/json",           # Added contentType
        accept="application/json",                # Added accept
        body=json.dumps({
            "prompt": prompt,                     # Use the prompt variable
            "max_tokens": max_tokens,             # Use the max_tokens variable
            "temperature": temperature            # Use the temperature variable
        })
    )
    # Parse the response
    response_body = json.loads(response['body'].read())
    return response_body["generations"][0]["text"]


def list_tuned_models():
    bedrock_client = boto3.client(service_name="bedrock",config=bedrock_config)
    models = []
    for model in bedrock_client.list_foundation_models(
        byCustomizationType="FINE_TUNING")["modelSummaries"]:
        models.append(model)
    return models

def train_model(model_id: str, dataset_name: str, output_model_name: str):
    bedrock_client = boto3.client(service_name="bedrock",config=bedrock_config)
    response = bedrock_client.start_foundation_model_tuning(
        modelId=model_id,
        trainingInput={
            "dataset_name": dataset_name,
            "output_model_name": output_model_name
        }
    )
    return response