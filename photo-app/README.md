# Q Dev Demo Reinforce Serverless Photo App

A serverless application for uploading and downloading photos using AWS services. This application demonstrates a modern serverless architecture using AWS Lambda, API Gateway, S3, and DynamoDB.

## Architecture

![Architecture Diagram](https://via.placeholder.com/800x400?text=Serverless+Photo+App+Architecture)

### Components

- **Frontend**: Simple HTML/CSS/JavaScript web interface
- **API Gateway**: HTTP API with two endpoints:
  - `POST /photos`: Upload photo and metadata
  - `GET /photos/{photoId}`: Download photo via pre-signed URL
- **Lambda Functions**:
  - `UploadPhotoFunction`: Processes uploads, stores in S3, and saves metadata to DynamoDB
  - `GetPhotoFunction`: Retrieves photo metadata and generates pre-signed S3 URLs
- **S3**: Private bucket for secure photo storage
- **DynamoDB**: NoSQL database for storing photo metadata

### Data Flow

1. **Upload Flow**:
   - User selects a photo in the web interface
   - Frontend encodes the photo as base64 and sends it to the API
   - API Gateway triggers the Upload Lambda function
   - Lambda stores the photo in S3 and metadata in DynamoDB
   - A unique photo ID is returned to the user

2. **Download Flow**:
   - User requests a photo by ID
   - API Gateway triggers the Get Lambda function
   - Lambda retrieves metadata from DynamoDB and generates a pre-signed URL
   - The pre-signed URL is returned to the user for secure, time-limited access

## Prerequisites

- [AWS Account](https://aws.amazon.com/)
- [AWS CLI](https://aws.amazon.com/cli/) configured with appropriate credentials
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
- [Python 3.9+](https://www.python.org/downloads/)

## Setup and Deployment

### Local Development

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd photo-app
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r src/upload_photo/requirements.txt
   pip install -r src/get_photo/requirements.txt
   pip install pytest  # For running tests
   ```

4. **Run tests**:
   ```bash
   pytest tests/
   ```

5. **Local API testing with SAM**:
   ```bash
   sam local start-api
   ```

6. **Test the frontend locally**:
   - Open `src/frontend/index.html` in a web browser
   - Update the `API_ENDPOINT` variable in the JavaScript code to point to your local or deployed API

### AWS Deployment

1. **Build the SAM application**:
   ```bash
   sam build
   ```

2. **Deploy to AWS**:
   ```bash
   sam deploy --guided
   ```
   - Follow the prompts to configure your deployment
   - Note the outputs, including the API endpoint URL

3. **Upload the frontend to S3**:
   ```bash
   # Update API_ENDPOINT in index.html with your deployed API URL
   aws s3 cp src/frontend/index.html s3://photo-app-frontend-{account-id}-{stage}/
   ```

4. **Access the application**:
   - Use the WebsiteURL from the CloudFormation outputs

## Security Considerations

- **Least Privilege**: IAM roles are configured with minimal permissions
- **Private S3 Bucket**: Photos are stored in a private bucket, accessible only via pre-signed URLs
- **URL Expiration**: Pre-signed URLs expire after a configurable time (default: 1 hour)
- **CORS**: API configured with appropriate CORS headers for web security

## Assumptions and Design Decisions

1. **Authentication**: This demo does not include user authentication. In a production environment, you would integrate with Amazon Cognito or another auth provider.

2. **File Size Limits**: API Gateway has a payload size limit (10MB by default). For larger files, consider using S3 pre-signed URLs for direct uploads.

3. **Error Handling**: The application includes basic error handling. A production system would need more comprehensive error handling and monitoring.

4. **Scalability**: The serverless architecture automatically scales with demand. DynamoDB is configured with on-demand capacity for automatic scaling.

5. **Cost Optimization**: Lambda functions are configured with minimal memory and timeout settings. S3 lifecycle policies can be adjusted to reduce storage costs.

## Future Enhancements

- User authentication and authorization
- Image processing (resizing, thumbnails, etc.)
- Album organization
- Sharing capabilities
- Mobile app integration

## License

[MIT License](LICENSE)

## Contact

For questions or support, please contact [your-email@example.com](mailto:your-email@example.com).