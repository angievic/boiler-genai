import boto3
from botocore.exceptions import NoCredentialsError, ClientError

def upload_file_to_s3(file_name, bucket, object_name=None):
    # Create an S3 client
    s3_client = boto3.client('s3')

    # If no object name is provided, use the file name
    if object_name is None:
        object_name = file_name

    try:
        # Upload the file
        s3_client.upload_file(file_name, bucket, object_name)
        print(f"Successfully uploaded {file_name} to {bucket}/{object_name}")

        # Construct the URL for the uploaded file
        file_url = f"https://{bucket}.s3.amazonaws.com/{object_name}"
        return file_url
    except FileNotFoundError:
        print(f"The file {file_name} was not found.")
        return None
    except NoCredentialsError:
        print("Credentials not available.")
        return None
    except ClientError as e:
        print(f"Failed to upload {file_name} to {bucket}/{object_name}: {e}")
        return None