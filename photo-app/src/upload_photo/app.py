import json
import os
import uuid
import base64
import boto3
from datetime import datetime

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Get environment variables
BUCKET_NAME = os.environ.get('PHOTOS_BUCKET')
TABLE_NAME = os.environ.get('PHOTOS_TABLE')

def lambda_handler(event, context):
    """
    Lambda function to handle photo uploads.
    
    This function:
    1. Receives a base64 encoded image and metadata from API Gateway
    2. Decodes the image
    3. Generates a unique ID for the photo
    4. Uploads the photo to S3
    5. Stores metadata in DynamoDB
    6. Returns the photo ID and other relevant information
    
    Args:
        event: API Gateway event containing the photo data and metadata
        context: Lambda context
        
    Returns:
        API Gateway response with status code and photo information
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Extract file data and metadata
        file_content = body.get('fileContent')
        file_name = body.get('fileName')
        
        # Validate input
        if not file_content or not file_name:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Missing required fields: fileContent or fileName'})
            }
        
        # Decode base64 file content
        file_content_decoded = base64.b64decode(file_content)
        
        # Generate unique photo ID
        photo_id = str(uuid.uuid4())
        
        # Generate S3 key
        s3_key = f"{photo_id}/{file_name}"
        
        # Upload to S3
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=file_content_decoded,
            ContentType=get_content_type(file_name)
        )
        
        # Get current timestamp
        timestamp = datetime.now().isoformat()
        
        # Store metadata in DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        table.put_item(
            Item={
                'photoId': photo_id,
                'fileName': file_name,
                'uploadTimestamp': timestamp,
                's3Key': s3_key
            }
        )
        
        # Return success response
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'photoId': photo_id,
                'fileName': file_name,
                'uploadTimestamp': timestamp,
                's3Key': s3_key
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }

def get_content_type(file_name):
    """
    Determine the content type based on file extension
    
    Args:
        file_name: Name of the file
        
    Returns:
        Content type string
    """
    extension = file_name.lower().split('.')[-1]
    content_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'webp': 'image/webp'
    }
    return content_types.get(extension, 'application/octet-stream')