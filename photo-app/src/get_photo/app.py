import json
import os
import boto3
import logging
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Get environment variables
BUCKET_NAME = os.environ.get('PHOTOS_BUCKET')
TABLE_NAME = os.environ.get('PHOTOS_TABLE')
URL_EXPIRATION = int(os.environ.get('URL_EXPIRATION', 3600))  # Default to 1 hour

def lambda_handler(event, context):
    """
    Lambda function to retrieve photo download URLs.
    
    This function:
    1. Receives a photo ID from the API Gateway path parameter
    2. Looks up the photo metadata in DynamoDB
    3. Generates a pre-signed URL for downloading the photo from S3
    
    Args:
        event (dict): API Gateway event
        context (object): Lambda context
        
    Returns:
        dict: API Gateway response with pre-signed URL
    """
    try:
        logger.info("Processing get photo request")
        
        # Extract photo ID from path parameters
        if 'pathParameters' not in event or not event['pathParameters'] or 'photoId' not in event['pathParameters']:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Missing photoId parameter'})
            }
            
        photo_id = event['pathParameters']['photoId']
        logger.info(f"Retrieving photo with ID: {photo_id}")
        
        # Look up photo metadata in DynamoDB
        try:
            table = dynamodb.Table(TABLE_NAME)
            response = table.get_item(Key={'photoId': photo_id})
            
            if 'Item' not in response:
                logger.warning(f"Photo with ID {photo_id} not found")
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Photo not found'})
                }
                
            photo_metadata = response['Item']
            s3_key = photo_metadata['s3Key']
            file_name = photo_metadata['fileName']
            
        except ClientError as e:
            logger.error(f"Error retrieving metadata from DynamoDB: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Failed to retrieve photo metadata'})
            }
        
        # Generate pre-signed URL for S3 object
        try:
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': BUCKET_NAME,
                    'Key': s3_key,
                    'ResponseContentDisposition': f'attachment; filename="{file_name}"'
                },
                ExpiresIn=URL_EXPIRATION
            )
            logger.info(f"Generated pre-signed URL for photo ID: {photo_id}")
            
        except ClientError as e:
            logger.error(f"Error generating pre-signed URL: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Failed to generate download URL'})
            }
        
        # Return success response with pre-signed URL and metadata
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'photoId': photo_id,
                'fileName': file_name,
                'uploadTimestamp': photo_metadata.get('uploadTimestamp'),
                'downloadUrl': presigned_url
            })
        }
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }