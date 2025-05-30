# Serverless Photo Application

A serverless application for uploading and downloading photos using AWS services. This application provides a simple and scalable way to store and retrieve photos using a serverless architecture.

## Architecture

![Architecture Diagram](https://via.placeholder.com/800x400?text=Photo+App+Architecture+Diagram)

### Components

- **Frontend**: Simple HTML/CSS/JavaScript application for uploading and viewing photos
- **API Gateway**: HTTP API with endpoints for uploading and retrieving photos
- **Lambda Functions**: Serverless functions for handling photo uploads and retrievals
- **S3**: Storage for the uploaded photos
- **DynamoDB**: Database for storing photo metadata

### API Endpoints

- `POST /photos`: Upload a photo and its metadata
- `GET /photos/{photoId}`: Get a photo by ID (returns pre-signed URL for download)

## Prerequisites

- [AWS Account](https://aws.amazon.com/)
- [AWS CLI](https://aws.amazon.com/cli/) configured with appropriate permissions
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
- [Python 3.9+](https://www.python.org/downloads/)
- [Node.js](https://nodejs.org/) (for local frontend development)

## Setup and Deployment

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/photo-app.git
cd photo-app
```

### 2. Install Dependencies

```bash
# Install Python dependencies for local development
pip install -r src/upload_photo/requirements.txt
pip install -r src/get_photo/requirements.txt

# Install test dependencies
pip install pytest pytest-mock
```

### 3. Run Tests

```bash
# Run unit tests
pytest tests/unit/
```

### 4. Deploy to AWS

```bash
# Build and deploy using SAM
sam build
sam deploy --guided
```

During the guided deployment, you'll be prompted for:
- Stack Name: (e.g., photo-app)
- AWS Region: (e.g., us-east-1)
- Confirm changes before deployment: (Y/n)
- Allow SAM CLI IAM role creation: (Y/n)
- Disable rollback: (y/N)

### 5. Update Frontend Configuration

After deployment, update the API URL in the frontend code:

1. Open `src/frontend/app.js`
2. Replace the `API_URL` value with your deployed API Gateway URL

### 6. Test the Application

You can test the application locally by:

```bash
# Serve the frontend locally
cd src/frontend
python -m http.server 8000
```

Then open your browser to http://localhost:8000

## Local Development

### Running Lambda Functions Locally

You can use SAM CLI to run the Lambda functions locally:

```bash
# Start API locally
sam local start-api

# Invoke a specific function
sam local invoke UploadPhotoFunction --event events/upload_event.json
```

### Testing the Frontend

The frontend can be tested locally without deploying to AWS. It uses local storage to simulate the backend functionality for development purposes.

## Security Considerations

- The S3 bucket is configured as private, and objects are accessed only through pre-signed URLs
- Lambda functions follow the principle of least privilege with specific IAM permissions
- API Gateway endpoints can be further secured with authentication mechanisms (e.g., AWS Cognito)

## Future Enhancements

- Add user authentication and authorization
- Implement photo sharing functionality
- Add image processing capabilities (resizing, filters, etc.)
- Create mobile applications using the same backend

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.