import json
import os
import uuid
import base64
import boto3
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
    1. Receives photo data and metadata from API Gateway
    2. Uploads the photo to S3
    3. Stores metadata in DynamoDB
    
    Args:
        event (dict): API Gateway event
        context (object): Lambda context
        
    Returns:
        dict: API Gateway response
    """
    try:
        logger.info("Processing upload request")
        
        # Parse request body
        if 'body' not in event:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Missing request body'})
            }
            
        # Check if body is base64 encoded
        if event.get('isBase64Encoded', False):
            body = json.loads(base64.b64decode(event['body']))
        else:
            body = json.loads(event['body'])
        
        # Validate required fields
        if 'fileName' not in body or 'fileContent' not in body:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Missing required fields: fileName and fileContent'})
            }
        
        file_name = body['fileName']
        file_content = body['fileContent']
        
        # Decode base64 file content
        try:
            file_bytes = base64.b64decode(file_content)
        except Exception as e:
            logger.error(f"Error decoding file content: {str(e)}")
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Invalid file content encoding'})
            }
        
        # Generate unique photo ID and S3 key
        photo_id = str(uuid.uuid4())
        s3_key = f"photos/{photo_id}/{file_name}"
        timestamp = datetime.utcnow().isoformat()
        
        # Upload file to S3
        try:
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=s3_key,
                Body=file_bytes,
                ContentType=body.get('contentType', 'image/jpeg')  # Default to JPEG if not specified
            )
            logger.info(f"File uploaded to S3: {s3_key}")
        except Exception as e:
            logger.error(f"Error uploading to S3: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Failed to upload file to S3'})
            }
        
        # Store metadata in DynamoDB
        try:
            table = dynamodb.Table(TABLE_NAME)
            table.put_item(
                Item={
                    'photoId': photo_id,
                    'fileName': file_name,
                    'uploadTimestamp': timestamp,
                    's3Key': s3_key
                }
            )
            logger.info(f"Metadata stored in DynamoDB for photo ID: {photo_id}")
        except Exception as e:
            logger.error(f"Error storing metadata in DynamoDB: {str(e)}")
            # If DynamoDB fails, try to delete the S3 object to maintain consistency
            try:
                s3_client.delete_object(Bucket=BUCKET_NAME, Key=s3_key)
            except Exception as delete_error:
                logger.error(f"Error deleting S3 object after DynamoDB failure: {str(delete_error)}")
            
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Failed to store metadata'})
            }
        
        # Return success response with photo ID
        return {
            'statusCode': 201,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'photoId': photo_id,
                'message': 'Photo uploaded successfully'
            })
        }
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }