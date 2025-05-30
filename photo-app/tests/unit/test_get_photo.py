import json
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from botocore.exceptions import ClientError

# Add the Lambda function directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/get_photo'))

# Import the Lambda function
import app

class TestGetPhotoFunction(unittest.TestCase):
    """Test cases for the get_photo Lambda function"""

    @patch('app.boto3.client')
    @patch('app.boto3.resource')
    def test_successful_retrieval(self, mock_resource, mock_client):
        """Test successful photo retrieval"""
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = "https://test-presigned-url.com"
        mock_client.return_value = mock_s3
        
        # Mock DynamoDB table and response
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'photoId': 'test-photo-id',
                'fileName': 'test_image.jpg',
                'uploadTimestamp': '2023-01-01T12:00:00',
                's3Key': 'test-photo-id/test_image.jpg'
            }
        }
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_resource.return_value = mock_dynamodb
        
        # Create test event
        event = {
            'pathParameters': {
                'photoId': 'test-photo-id'
            }
        }
        
        # Set environment variables
        os.environ['PHOTOS_BUCKET'] = 'test-bucket'
        os.environ['PHOTOS_TABLE'] = 'test-table'
        os.environ['URL_EXPIRATION'] = '3600'
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify response
        self.assertEqual(response['statusCode'], 200)
        
        # Parse response body
        response_body = json.loads(response['body'])
        
        # Verify response data
        self.assertEqual(response_body['photoId'], 'test-photo-id')
        self.assertEqual(response_body['fileName'], 'test_image.jpg')
        self.assertEqual(response_body['s3Key'], 'test-photo-id/test_image.jpg')
        self.assertEqual(response_body['downloadUrl'], 'https://test-presigned-url.com')
        
        # Verify S3 generate_presigned_url was called
        mock_s3.generate_presigned_url.assert_called_once_with(
            'get_object',
            Params={
                'Bucket': 'test-bucket',
                'Key': 'test-photo-id/test_image.jpg'
            },
            ExpiresIn=3600
        )
        
        # Verify DynamoDB get_item was called
        mock_table.get_item.assert_called_once_with(
            Key={
                'photoId': 'test-photo-id'
            }
        )
    
    def test_missing_photo_id(self):
        """Test handling of missing photo ID"""
        # Test with missing photoId
        event_missing_id = {
            'pathParameters': {}
        }
        
        response = app.lambda_handler(event_missing_id, {})
        self.assertEqual(response['statusCode'], 400)
        
        # Test with no pathParameters
        event_no_params = {}
        
        response = app.lambda_handler(event_no_params, {})
        self.assertEqual(response['statusCode'], 400)
    
    @patch('app.boto3.client')
    @patch('app.boto3.resource')
    def test_photo_not_found(self, mock_resource, mock_client):
        """Test handling of non-existent photo"""
        # Mock DynamoDB table and response for non-existent item
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}  # No Item in response
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_resource.return_value = mock_dynamodb
        
        # Create test event
        event = {
            'pathParameters': {
                'photoId': 'non-existent-id'
            }
        }
        
        # Set environment variables
        os.environ['PHOTOS_TABLE'] = 'test-table'
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify response
        self.assertEqual(response['statusCode'], 404)
    
    @patch('app.boto3.client')
    @patch('app.boto3.resource')
    def test_presigned_url_error(self, mock_resource, mock_client):
        """Test handling of errors when generating presigned URL"""
        # Mock S3 client to raise an exception
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.side_effect = ClientError(
            {'Error': {'Code': 'TestException', 'Message': 'Test error message'}},
            'generate_presigned_url'
        )
        mock_client.return_value = mock_s3
        
        # Mock DynamoDB table and response
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'photoId': 'test-photo-id',
                'fileName': 'test_image.jpg',
                'uploadTimestamp': '2023-01-01T12:00:00',
                's3Key': 'test-photo-id/test_image.jpg'
            }
        }
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_resource.return_value = mock_dynamodb
        
        # Create test event
        event = {
            'pathParameters': {
                'photoId': 'test-photo-id'
            }
        }
        
        # Set environment variables
        os.environ['PHOTOS_BUCKET'] = 'test-bucket'
        os.environ['PHOTOS_TABLE'] = 'test-table'
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify response
        self.assertEqual(response['statusCode'], 500)

if __name__ == '__main__':
    unittest.main()