# Azure Deployment Guide

This application is designed to be deployed to Azure App Service. Follow these steps to troubleshoot deployment issues:

## Deployment Files

The most critical files for Azure deployment are:

1. **web.config** - Instructs Azure how to start the application
2. **startup.sh** - The script that boots the application
3. **deploy.sh** - Prepares files during deployment

## Troubleshooting Steps

If you're seeing the default Azure welcome page, it means the application is not starting correctly. Try these steps:

1. In the Azure Portal, go to your App Service
2. Navigate to **Development Tools** > **Advanced Tools** > **Go** (Kudu)
3. Click on **Debug Console** > **CMD** or **PowerShell**
4. Navigate to `site/wwwroot`
5. Check if all files were deployed correctly:
   ```
   dir
   ```
   
6. Verify the startup script is executable:
   ```
   chmod +x startup.sh
   ```
   
7. Check application logs:
   ```
   cat /home/LogFiles/stdout.log
   ```
   
8. Also check for the debug log:
   ```
   cat azure-debug.log
   ```

## Manual Deployment

If GitHub Actions deployment is failing, you can deploy manually:

1. Build the application locally:
   ```
   cd frontend
   npm run build
   cd ..
   ```
   
2. Zip all files (excluding node_modules, etc.)
   
3. Upload via Kudu console or using the Azure CLI:
   ```
   az webapp deployment source config-zip --resource-group <group-name> --name <app-name> --src <zip-file>
   ```

## Configuration

Ensure these settings are configured in the Azure Portal:

1. **General Settings**:
   - Stack: Python
   - Python Version: 3.11
   
2. **Application Settings**:
   - SCM_DO_BUILD_DURING_DEPLOYMENT: true
   - POST_BUILD_COMMAND: chmod +x startup.sh && chmod +x deploy.sh
   - WEBSITE_RUN_FROM_PACKAGE: 0 