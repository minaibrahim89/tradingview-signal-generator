import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Card,
  CardContent,
  CardActions,
  TextField,
  Divider,
  Alert,
  AlertTitle,
  Grid,
  Link,
} from '@mui/material';
import { UploadFile as UploadIcon, Refresh as RefreshIcon } from '@mui/icons-material';

function Settings() {
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState({
    loading: false,
    success: false,
    error: null,
  });

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    setFile(selectedFile);
  };

  const handleUpload = () => {
    if (!file) return;

    // This is a mock implementation - in a real app you'd send the file to the server
    setUploadStatus({ loading: true, success: false, error: null });

    // Simulate API call
    setTimeout(() => {
      // Check if file is named credentials.json
      if (file.name !== 'credentials.json') {
        setUploadStatus({
          loading: false,
          success: false,
          error: 'The file must be named credentials.json',
        });
        return;
      }

      setUploadStatus({
        loading: false,
        success: true,
        error: null,
      });
    }, 1500);
  };

  const handleResetAuth = () => {
    if (window.confirm('Are you sure you want to reset authentication? You will need to re-authenticate with Google.')) {
      // Mock implementation - would send a request to the server
      alert('Authentication reset! You will need to restart the application to re-authenticate.');
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Gmail API Credentials
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Upload your Google Cloud OAuth credentials to connect your Gmail account.
              </Typography>

              <Alert severity="info" sx={{ mb: 2 }}>
                <AlertTitle>How to get credentials</AlertTitle>
                1. Go to the <Link href="https://console.cloud.google.com" target="_blank" rel="noopener">Google Cloud Console</Link>
                <br />
                2. Create a project and enable the Gmail API
                <br />
                3. Create OAuth credentials for a desktop application
                <br />
                4. Download the credentials JSON file and rename it to <strong>credentials.json</strong>
              </Alert>

              <Box sx={{ my: 2 }}>
                <input
                  accept=".json"
                  style={{ display: 'none' }}
                  id="credentials-file"
                  type="file"
                  onChange={handleFileChange}
                />
                <label htmlFor="credentials-file">
                  <Button
                    variant="outlined"
                    component="span"
                    startIcon={<UploadIcon />}
                  >
                    Select File
                  </Button>
                </label>
                {file && (
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    Selected file: {file.name}
                  </Typography>
                )}
              </Box>

              {uploadStatus.error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {uploadStatus.error}
                </Alert>
              )}

              {uploadStatus.success && (
                <Alert severity="success" sx={{ mb: 2 }}>
                  Credentials uploaded successfully! You will need to restart the application to use the new credentials.
                </Alert>
              )}
            </CardContent>
            <CardActions>
              <Button
                variant="contained"
                onClick={handleUpload}
                disabled={!file || uploadStatus.loading}
              >
                Upload Credentials
              </Button>
            </CardActions>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Authentication Reset
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                If you're having issues with Google authentication or want to use a different account, you can reset the authentication.
              </Typography>

              <Alert severity="warning">
                <AlertTitle>Warning</AlertTitle>
                Resetting authentication will delete the current token and require you to re-authenticate with Google.
                The email processor will stop until re-authentication is complete.
              </Alert>
            </CardContent>
            <CardActions>
              <Button
                variant="outlined"
                color="error"
                startIcon={<RefreshIcon />}
                onClick={handleResetAuth}
              >
                Reset Authentication
              </Button>
            </CardActions>
          </Card>
        </Grid>
      </Grid>

      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Environment Configuration
        </Typography>
        <Divider sx={{ mb: 2 }} />
        
        <Typography variant="body2" color="text.secondary" paragraph>
          These settings are configured in the .env file. To modify them, stop the application, edit the .env file, and restart.
        </Typography>
        
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Port"
              defaultValue="8000"
              InputProps={{ readOnly: true }}
              variant="filled"
              helperText="Application port (APP_PORT)"
              size="small"
              margin="normal"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Credentials Path"
              defaultValue="credentials.json"
              InputProps={{ readOnly: true }}
              variant="filled"
              helperText="Path to Google credentials file (GMAIL_CREDENTIALS_PATH)"
              size="small"
              margin="normal"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Token Path"
              defaultValue="token.json"
              InputProps={{ readOnly: true }}
              variant="filled"
              helperText="Path to OAuth token file (GMAIL_TOKEN_PATH)"
              size="small"
              margin="normal"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Authentication Method"
              defaultValue="Headless (console-based)"
              InputProps={{ readOnly: true }}
              variant="filled"
              helperText="Method for Google authentication (USE_LOCAL_SERVER_AUTH)"
              size="small"
              margin="normal"
            />
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
}

export default Settings; 