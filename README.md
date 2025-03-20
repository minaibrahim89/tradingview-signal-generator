# Trading View Signal Generator

A FastAPI application that monitors Gmail for trading signals and forwards them to webhooks.

## Features

* Monitor Gmail inbox for trading signals via email
* Filter emails by sender, subject, etc.
* Forward email content to configurable webhooks
* Track processed emails to avoid duplicates
* Web interface for configuration and monitoring

## Deployment on Azure

This application is configured for deployment on Azure App Service. The deployment process has been simplified to ensure reliable operation.

### Deployment Process

1. The GitHub workflow builds the application and deploys it to Azure App Service.
2. Static files are copied directly to the deployment package (no .tar.gz files involved).
3. During startup, any leftover .tar.gz files are automatically removed.
4. Scripts ensure the application starts properly with all required dependencies.

### Important Files

- **startup.sh**: Main entry script for Azure App Service
- **deploy.sh**: Additional deployment script
- **main.py**: Main application file
- **requirements.txt**: Python dependencies

## Development

### Local Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Set up Gmail API credentials:
   - Place `credentials.json` in the root directory
   - Or set environment variables: `CLIENT_ID`, `CLIENT_SECRET`, `REFRESH_TOKEN`

5. Run the application:
   ```
   python main.py
   ```

### Frontend Development

The frontend uses Vite and React:

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```
2. Install dependencies:
   ```
   npm install
   ```
3. Start the development server:
   ```
   npm run dev
   ```

## Endpoints

- **API**: `/api/v1/...`
- **Health Check**: `/health`
- **Documentation**: `/docs`
- **Frontend**: `/`

## Troubleshooting

If you encounter deployment issues:

1. Check the application logs on Azure App Service
2. Verify the health endpoint is responding correctly
3. Ensure all required credentials are available

## License

[MIT License](LICENSE)
