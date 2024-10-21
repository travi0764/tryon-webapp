import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import NoCredentialsError

load_dotenv()

# Initialize the S3 client
def initialize_s3_client():
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv("AWS_ACESS_KEY"),
        aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
        region_name="eu-north-1"
    )
    return s3


def upload_file_to_s3(file_path, bucket_name, object_name=None):
    """Upload a file to an S3 bucket and return the public URL."""
    # If no object name is provided, use the file name
    if object_name is None:
        object_name = file_path.split('/')[-1]
    
    s3 = initialize_s3_client()

    # Detect the content type of the image (you can hardcode it if needed)
    if file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
        content_type = "image/jpeg"
    elif file_path.endswith(".png"):
        content_type = "image/png"
    elif file_path.endswith(".gif"):
        content_type = "image/gif"
    else:
        content_type = "application/octet-stream"  # Default fallback

    try:
        # Upload the file to S3 with the correct content type (without ACL)
        s3.upload_file(
            file_path, 
            bucket_name, 
            object_name, 
            ExtraArgs={
                'ContentType': content_type  # Set the content type
            }
        )

        # Generate the public URL
        public_url = f"https://{bucket_name}.s3.amazonaws.com/{object_name}"
        return public_url

    except FileNotFoundError:
        print("The file was not found")
    except NoCredentialsError:
        print("Credentials not available")


