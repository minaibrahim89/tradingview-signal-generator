# Azure Deployment Guide

This guide explains the simplified deployment process for the Trading View Signal Generator application on Azure Web App.

## Key Files

- **web.config**: Tells Azure how to start your application
- **startup.sh**: Main script that starts your application
- **deploy.sh**: Handles deployment tasks
- **cleanup.sh**: Removes any tar.gz files
- **.deployment**: Configuration for Azure Kudu deployment engine
- **diagnostic.py**: Helps diagnose deployment issues

## Deployment Flow

1. **GitHub Actions** builds the application and packages it for deployment
2. The package is uploaded to Azure Web App
3. `.deployment` file tells Azure to run `deploy.sh`
4. `deploy.sh` handles initial setup
5. `web.config` tells Azure to use `startup.sh` for running the application
6. `startup.sh` runs `cleanup.sh` and then starts the web server
7. `cleanup.sh` removes any leftover tar.gz files

## Troubleshooting

If the application doesn't deploy correctly:

1. **Check logs**: Navigate to your Azure Web App → Log stream
2. **Run diagnostic script**: SSH into your Web App and run `python diagnostic.py`
3. **Verify files**: Ensure all key files exist in `/home/site/wwwroot/`
4. **Check for tar.gz files**: Make sure no tar.gz files exist in the wwwroot directory
5. **Restart the app**: Try restarting the web app from the Azure portal

## Manual Deployment

If GitHub Actions doesn't work, you can deploy manually:

1. Build the application locally
2. Zip the entire application directory
3. Deploy through the Azure portal using the "Deploy from ZIP" option

## Important Notes

- The application is hosted in `/home/site/wwwroot/` on Azure
- Static files are served from the `static` directory
- The startup script automatically creates a static directory if missing
- The cleanup script is crucial for removing any leftover tar.gz files that might interfere with proper operation

## Configuration

Ensure these settings are configured in the Azure Portal:

1. **General Settings**:
   - Stack: Python
   - Python Version: 3.11
   
2. **Application Settings**:
   - SCM_DO_BUILD_DURING_DEPLOYMENT: true
   - POST_BUILD_COMMAND: chmod +x startup.sh && chmod +x deploy.sh
   - WEBSITE_RUN_FROM_PACKAGE: 0 