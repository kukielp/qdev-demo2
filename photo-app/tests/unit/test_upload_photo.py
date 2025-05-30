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

    @patch('app.boto3.client')
    @patch('app.boto3.resource')
    @patch('app.uuid.uuid4')
    def test_successful_upload(self, mock_uuid, mock_resource, mock_client):
        """Test successful photo upload"""
        # Mock UUID
        mock_uuid_value = "12345678-1234-5678-1234-567812345678"
        mock_uuid.return_value = mock_uuid_value
        
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_client.return_value = mock_s3
        
        # Mock DynamoDB table
        mock_table = MagicMock()
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_resource.return_value = mock_dynamodb
        
        # Test data
        test_file_name = "test_image.jpg"
        test_file_content = base64.b64encode(b"test image content").decode('utf-8')
        
        # Create test event
        event = {
            'body': json.dumps({
                'fileName': test_file_name,
                'fileContent': test_file_content
            })
        }
        
        # Set environment variables
        os.environ['PHOTOS_BUCKET'] = 'test-bucket'
        os.environ['PHOTOS_TABLE'] = 'test-table'
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify response
        self.assertEqual(response['statusCode'], 201)
        
        # Parse response body
        response_body = json.loads(response['body'])
        
        # Verify response data
        self.assertEqual(response_body['photoId'], mock_uuid_value)
        self.assertEqual(response_body['fileName'], test_file_name)
        self.assertEqual(response_body['s3Key'], f"{mock_uuid_value}/{test_file_name}")
        
        # Verify S3 put_object was called
        mock_s3.put_object.assert_called_once()
        call_args = mock_s3.put_object.call_args[1]
        self.assertEqual(call_args['Bucket'], 'test-bucket')
        self.assertEqual(call_args['Key'], f"{mock_uuid_value}/{test_file_name}")
        self.assertEqual(call_args['ContentType'], 'image/jpeg')
        
        # Verify DynamoDB put_item was called
        mock_table.put_item.assert_called_once()
        item = mock_table.put_item.call_args[1]['Item']
        self.assertEqual(item['photoId'], mock_uuid_value)
        self.assertEqual(item['fileName'], test_file_name)
        self.assertEqual(item['s3Key'], f"{mock_uuid_value}/{test_file_name}")
    
    def test_missing_fields(self):
        """Test handling of missing required fields"""
        # Test with missing fileName
        event_missing_filename = {
            'body': json.dumps({
                'fileContent': 'test_content'
            })
        }
        
        response = app.lambda_handler(event_missing_filename, {})
        self.assertEqual(response['statusCode'], 400)
        
        # Test with missing fileContent
        event_missing_content = {
            'body': json.dumps({
                'fileName': 'test.jpg'
            })
        }
        
        response = app.lambda_handler(event_missing_content, {})
        self.assertEqual(response['statusCode'], 400)
    
    @patch('app.boto3.client')
    @patch('app.boto3.resource')
    def test_s3_error_handling(self, mock_resource, mock_client):
        """Test handling of S3 errors"""
        # Mock S3 client to raise an exception
        mock_s3 = MagicMock()
        mock_s3.put_object.side_effect = Exception("S3 error")
        mock_client.return_value = mock_s3
        
        # Mock DynamoDB
        mock_dynamodb = MagicMock()
        mock_resource.return_value = mock_dynamodb
        
        # Test data
        event = {
            'body': json.dumps({
                'fileName': 'test.jpg',
                'fileContent': base64.b64encode(b"test content").decode('utf-8')
            })
        }
        
        # Set environment variables
        os.environ['PHOTOS_BUCKET'] = 'test-bucket'
        os.environ['PHOTOS_TABLE'] = 'test-table'
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify response
        self.assertEqual(response['statusCode'], 500)
        
    def test_content_type_detection(self):
        """Test content type detection for different file extensions"""
        self.assertEqual(app.get_content_type('test.jpg'), 'image/jpeg')
        self.assertEqual(app.get_content_type('test.jpeg'), 'image/jpeg')
        self.assertEqual(app.get_content_type('test.png'), 'image/png')
        self.assertEqual(app.get_content_type('test.gif'), 'image/gif')
        self.assertEqual(app.get_content_type('test.bmp'), 'image/bmp')
        self.assertEqual(app.get_content_type('test.webp'), 'image/webp')
        self.assertEqual(app.get_content_type('test.unknown'), 'application/octet-stream')

if __name__ == '__main__':
    unittest.main()