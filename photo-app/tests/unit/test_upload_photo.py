import json
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import uuid
import base64

# Add the Lambda function directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/upload_photo'))

# Import the Lambda function
import app

class TestUploadPhotoFunction(unittest.TestCase):
    """Test cases for the upload_photo Lambda function"""

    def setUp(self):
        """Set up test fixtures before each test"""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'PHOTOS_BUCKET': 'test-photos-bucket',
            'PHOTOS_TABLE': 'test-photos-table'
        })
        self.env_patcher.start()
        
        # Mock UUID generation to return a predictable value
        self.uuid_patcher = patch('uuid.uuid4')
        self.mock_uuid = self.uuid_patcher.start()
        self.mock_uuid.return_value = 'test-uuid-1234'
        
        # Sample test data
        self.test_file_name = 'test-image.jpg'
        self.test_file_content = base64.b64encode(b'test image content').decode('utf-8')
        self.test_content_type = 'image/jpeg'

    def tearDown(self):
        """Tear down test fixtures after each test"""
        self.env_patcher.stop()
        self.uuid_patcher.stop()

    @patch('app.s3_client')
    @patch('app.dynamodb.Table')
    def test_successful_upload(self, mock_table, mock_s3_client):
        """Test successful photo upload"""
        # Mock S3 and DynamoDB responses
        mock_s3_client.put_object.return_value = {}
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.put_item.return_value = {}
        
        # Create test event
        event = {
            'body': json.dumps({
                'fileName': self.test_file_name,
                'fileContent': self.test_file_content,
                'contentType': self.test_content_type
            }),
            'isBase64Encoded': False
        }
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 201)
        response_body = json.loads(response['body'])
        self.assertEqual(response_body['photoId'], 'test-uuid-1234')
        self.assertEqual(response_body['message'], 'Photo uploaded successfully')
        
        # Verify S3 was called correctly
        mock_s3_client.put_object.assert_called_once()
        s3_args = mock_s3_client.put_object.call_args[1]
        self.assertEqual(s3_args['Bucket'], 'test-photos-bucket')
        self.assertEqual(s3_args['Key'], f"photos/test-uuid-1234/{self.test_file_name}")
        self.assertEqual(s3_args['ContentType'], self.test_content_type)
        
        # Verify DynamoDB was called correctly
        mock_table_instance.put_item.assert_called_once()
        ddb_args = mock_table_instance.put_item.call_args[1]
        self.assertEqual(ddb_args['Item']['photoId'], 'test-uuid-1234')
        self.assertEqual(ddb_args['Item']['fileName'], self.test_file_name)
        self.assertEqual(ddb_args['Item']['s3Key'], f"photos/test-uuid-1234/{self.test_file_name}")

    @patch('app.s3_client')
    @patch('app.dynamodb.Table')
    def test_missing_required_fields(self, mock_table, mock_s3_client):
        """Test handling of missing required fields"""
        # Create test event with missing fileName
        event = {
            'body': json.dumps({
                'fileContent': self.test_file_content,
                'contentType': self.test_content_type
            }),
            'isBase64Encoded': False
        }
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        
        # Verify S3 and DynamoDB were not called
        mock_s3_client.put_object.assert_not_called()
        mock_table.return_value.put_item.assert_not_called()

    @patch('app.s3_client')
    @patch('app.dynamodb.Table')
    def test_s3_upload_error(self, mock_table, mock_s3_client):
        """Test handling of S3 upload error"""
        # Mock S3 to raise an exception
        mock_s3_client.put_object.side_effect = Exception("S3 upload failed")
        
        # Create test event
        event = {
            'body': json.dumps({
                'fileName': self.test_file_name,
                'fileContent': self.test_file_content,
                'contentType': self.test_content_type
            }),
            'isBase64Encoded': False
        }
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        
        # Verify DynamoDB was not called
        mock_table.return_value.put_item.assert_not_called()

    @patch('app.s3_client')
    @patch('app.dynamodb.Table')
    def test_dynamodb_error(self, mock_table, mock_s3_client):
        """Test handling of DynamoDB error"""
        # Mock S3 success but DynamoDB failure
        mock_s3_client.put_object.return_value = {}
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.put_item.side_effect = Exception("DynamoDB put failed")
        
        # Create test event
        event = {
            'body': json.dumps({
                'fileName': self.test_file_name,
                'fileContent': self.test_file_content,
                'contentType': self.test_content_type
            }),
            'isBase64Encoded': False
        }
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        
        # Verify S3 delete was called to clean up
        mock_s3_client.delete_object.assert_called_once()

if __name__ == '__main__':
    unittest.main()