import json
import os
import boto3
from botocore.exceptions import ClientError

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Get environment variables
BUCKET_NAME = os.environ.get('PHOTOS_BUCKET')
TABLE_NAME = os.environ.get('PHOTOS_TABLE')
URL_EXPIRATION = int(os.environ.get('URL_EXPIRATION', '3600'))  # Default 1 hour

def lambda_handler(event, context):
    """
    Lambda function to retrieve photo information and generate a pre-signed URL.
    
    This function:
    1. Extracts the photo ID from the path parameters
    2. Retrieves the photo metadata from DynamoDB
    3. Generates a pre-signed URL for downloading the photo from S3
    4. Returns the photo metadata and pre-signed URL
    
    Args:
        event: API Gateway event containing the photo ID
        context: Lambda context
        
    Returns:
        API Gateway response with status code and photo information including pre-signed URL
    """
    try:
        # Extract photo ID from path parameters
        photo_id = event.get('pathParameters', {}).get('photoId')
        
        # Validate input
        if not photo_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Missing required parameter: photoId'})
            }
        
        # Get photo metadata from DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        response = table.get_item(
            Key={
                'photoId': photo_id
            }
        )
        
        # Check if photo exists
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': f'Photo with ID {photo_id} not found'})
            }
        
        # Get photo metadata
        photo_metadata = response['Item']
        s3_key = photo_metadata['s3Key']
        
        # Generate pre-signed URL
        try:
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': BUCKET_NAME,
                    'Key': s3_key
                },
                ExpiresIn=URL_EXPIRATION
            )
        except ClientError as e:
            print(f"Error generating presigned URL: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Failed to generate download URL'})
            }
        
        # Add presigned URL to response
        photo_metadata['downloadUrl'] = presigned_url
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(photo_metadata)
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