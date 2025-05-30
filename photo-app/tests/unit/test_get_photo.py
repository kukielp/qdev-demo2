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

    def setUp(self):
        """Set up test fixtures before each test"""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'PHOTOS_BUCKET': 'test-photos-bucket',
            'PHOTOS_TABLE': 'test-photos-table',
            'URL_EXPIRATION': '3600'
        })
        self.env_patcher.start()
        
        # Sample test data
        self.test_photo_id = 'test-photo-id-1234'
        self.test_file_name = 'test-image.jpg'
        self.test_s3_key = f'photos/{self.test_photo_id}/{self.test_file_name}'
        self.test_timestamp = '2023-01-01T12:00:00'
        self.test_presigned_url = 'https://test-bucket.s3.amazonaws.com/test-key?signature=abc123'

    def tearDown(self):
        """Tear down test fixtures after each test"""
        self.env_patcher.stop()

    @patch('app.s3_client')
    @patch('app.dynamodb.Table')
    def test_successful_get_photo(self, mock_table, mock_s3_client):
        """Test successful photo retrieval"""
        # Mock DynamoDB response
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {
            'Item': {
                'photoId': self.test_photo_id,
                'fileName': self.test_file_name,
                'uploadTimestamp': self.test_timestamp,
                's3Key': self.test_s3_key
            }
        }
        
        # Mock S3 presigned URL generation
        mock_s3_client.generate_presigned_url.return_value = self.test_presigned_url
        
        # Create test event
        event = {
            'pathParameters': {
                'photoId': self.test_photo_id
            }
        }
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 200)
        response_body = json.loads(response['body'])
        self.assertEqual(response_body['photoId'], self.test_photo_id)
        self.assertEqual(response_body['fileName'], self.test_file_name)
        self.assertEqual(response_body['uploadTimestamp'], self.test_timestamp)
        self.assertEqual(response_body['downloadUrl'], self.test_presigned_url)
        
        # Verify DynamoDB was called correctly
        mock_table_instance.get_item.assert_called_once_with(Key={'photoId': self.test_photo_id})
        
        # Verify S3 was called correctly
        mock_s3_client.generate_presigned_url.assert_called_once()
        s3_args = mock_s3_client.generate_presigned_url.call_args
        self.assertEqual(s3_args[0][0], 'get_object')
        self.assertEqual(s3_args[1]['Params']['Bucket'], 'test-photos-bucket')
        self.assertEqual(s3_args[1]['Params']['Key'], self.test_s3_key)
        self.assertEqual(s3_args[1]['ExpiresIn'], 3600)

    @patch('app.dynamodb.Table')
    def test_missing_photo_id(self, mock_table):
        """Test handling of missing photo ID"""
        # Create test event with missing photoId
        event = {
            'pathParameters': None
        }
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        
        # Verify DynamoDB was not called
        mock_table.return_value.get_item.assert_not_called()

    @patch('app.s3_client')
    @patch('app.dynamodb.Table')
    def test_photo_not_found(self, mock_table, mock_s3_client):
        """Test handling of photo not found in DynamoDB"""
        # Mock DynamoDB response for item not found
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {}  # No Item in response
        
        # Create test event
        event = {
            'pathParameters': {
                'photoId': self.test_photo_id
            }
        }
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 404)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        
        # Verify S3 was not called
        mock_s3_client.generate_presigned_url.assert_not_called()

    @patch('app.s3_client')
    @patch('app.dynamodb.Table')
    def test_dynamodb_error(self, mock_table, mock_s3_client):
        """Test handling of DynamoDB error"""
        # Mock DynamoDB to raise an exception
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.side_effect = ClientError(
            {'Error': {'Code': 'InternalServerError', 'Message': 'DynamoDB error'}},
            'GetItem'
        )
        
        # Create test event
        event = {
            'pathParameters': {
                'photoId': self.test_photo_id
            }
        }
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        
        # Verify S3 was not called
        mock_s3_client.generate_presigned_url.assert_not_called()

    @patch('app.s3_client')
    @patch('app.dynamodb.Table')
    def test_s3_presigned_url_error(self, mock_table, mock_s3_client):
        """Test handling of S3 presigned URL generation error"""
        # Mock DynamoDB response
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {
            'Item': {
                'photoId': self.test_photo_id,
                'fileName': self.test_file_name,
                'uploadTimestamp': self.test_timestamp,
                's3Key': self.test_s3_key
            }
        }
        
        # Mock S3 to raise an exception
        mock_s3_client.generate_presigned_url.side_effect = ClientError(
            {'Error': {'Code': 'InternalServerError', 'Message': 'S3 error'}},
            'GeneratePresignedUrl'
        )
        
        # Create test event
        event = {
            'pathParameters': {
                'photoId': self.test_photo_id
            }
        }
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)

if __name__ == '__main__':
    unittest.main()