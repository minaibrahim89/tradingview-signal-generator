import React, { useState, useEffect } from 'react';
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
  CircularProgress,
} from '@mui/material';
import { 
  Google as GoogleIcon,
  Refresh as RefreshIcon,
  Email as EmailIcon
} from '@mui/icons-material';
import { getAuthStatus, resetAuth, startGoogleAuth } from '../services/api';

function Settings() {
  const [authStatus, setAuthStatus] = useState({
    loading: true,
    is_authenticated: false,
    credentials_exist: false,
    token_exists: false,
    email: null,
  });

  // Load authentication status when component mounts
  useEffect(() => {
    fetchAuthStatus();
  }, []);

  const fetchAuthStatus = async () => {
    try {
      setAuthStatus(prev => ({ ...prev, loading: true }));
      const { data } = await getAuthStatus();
      setAuthStatus({
        loading: false,
        ...data
      });
    } catch (error) {
      console.error('Error fetching auth status:', error);
      setAuthStatus({
        loading: false,
        is_authenticated: false,
        credentials_exist: false,
        token_exists: false,
        error: 'Failed to load authentication status'
      });
    }
  };

  const handleResetAuth = async () => {
    if (window.confirm('Are you sure you want to reset authentication? You will need to re-authenticate with Google.')) {
      try {
        await resetAuth();
        alert('Authentication reset! You can now sign in with a different Google account.');
        // Refresh auth status
        fetchAuthStatus();
      } catch (error) {
        alert(`Error resetting authentication: ${error.message}`);
      }
    }
  };

  const handleGoogleSignIn = () => {
    startGoogleAuth();
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Gmail Account
      </Typography>
      
      {authStatus.loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Card sx={{ mb: 3, maxWidth: 600 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Gmail Account Status
            </Typography>
            
            {authStatus.is_authenticated ? (
              <>
                <Alert severity="success" sx={{ mb: 3 }}>
                  <AlertTitle>Connected to Gmail</AlertTitle>
                  You are signed in as <strong>{authStatus.email || 'Unknown user'}</strong>
                  <Box sx={{ mt: 1 }}>
                    The application is now monitoring this Gmail account for emails.
                  </Box>
                </Alert>
                
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<RefreshIcon />}
                  onClick={handleResetAuth}
                  size="small"
                >
                  Sign out
                </Button>
              </>
            ) : (
              <>
                <Alert severity="info" sx={{ mb: 3 }}>
                  <AlertTitle>Not connected to Gmail</AlertTitle>
                  Sign in with Google to start monitoring your Gmail account
                </Alert>
                
                <Button
                  variant="contained"
                  color="primary"
                  size="large"
                  startIcon={<GoogleIcon />}
                  onClick={handleGoogleSignIn}
                  fullWidth
                  sx={{ py: 1.5 }}
                >
                  Sign in with Google
                </Button>
                
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2, fontSize: '0.85rem' }}>
                  Note: This app will only read your emails (it cannot modify or send emails).
                  You can revoke access anytime from your Google account settings.
                </Typography>
              </>
            )}
          </CardContent>
        </Card>
      )}

      <Paper sx={{ p: 3, mt: 3, maxWidth: 800 }}>
        <Typography variant="h6" gutterBottom>
          How it works
        </Typography>
        <Divider sx={{ mb: 2 }} />
        
        <Typography variant="body2" paragraph>
          1. Sign in with your Google account to connect your Gmail
        </Typography>
        <Typography variant="body2" paragraph>
          2. Configure which emails to monitor in the Email Configurations section
        </Typography>
        <Typography variant="body2" paragraph>
          3. Set up webhooks to forward the email content
        </Typography>
        <Typography variant="body2" paragraph>
          4. The application will automatically check for new emails and forward them to your webhooks
        </Typography>
      </Paper>

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
              label="Redirect URI"
              defaultValue="http://localhost:5173"
              InputProps={{ readOnly: true }}
              variant="filled"
              helperText="OAuth redirect URI (GOOGLE_REDIRECT_URI)"
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