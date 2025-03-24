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
  Email as EmailIcon,
  Delete as DeleteIcon,
  PlayArrow as PlayArrowIcon
} from '@mui/icons-material';
import { getAuthStatus, resetAuth, startGoogleAuth, clearStateTokens, restartService } from '../services/api';

function Settings() {
  const [authStatus, setAuthStatus] = useState({
    loading: true,
    is_authenticated: false,
    credentials_exist: false,
    token_exists: false,
    email: null,
  });

  // Load authentication status when component mounts or when location changes (like after redirect)
  useEffect(() => {
    console.log("Settings component mounted or updated, fetching auth status");
    fetchAuthStatus();
    
    // Check if we were just redirected from auth flow
    const queryParams = new URLSearchParams(window.location.search);
    const authSuccess = queryParams.get('auth_success');
    
    if (authSuccess) {
      console.log("Auth success detected in query params, refreshing status");
      // Clear the URL parameter so refreshes don't trigger this again
      window.history.replaceState({}, document.title, window.location.pathname);
      
      // Add a small delay to ensure token is saved before checking status
      setTimeout(async () => {
        await fetchAuthStatus();
        // After fetching status, try to restart service to apply the new token
        try {
          console.log("Auto-restarting service after successful authentication...");
          await restartService();
          console.log("Service restarted successfully, refreshing status again...");
          // Refresh status again after restart
          await fetchAuthStatus();
        } catch (error) {
          console.error("Error auto-restarting service:", error);
        }
      }, 1000);
    }
  }, []);

  const fetchAuthStatus = async () => {
    try {
      console.log("Fetching auth status...");
      setAuthStatus(prev => ({ ...prev, loading: true }));
      const { data } = await getAuthStatus();
      console.log("Auth status response:", data);
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

  const handleClearStateTokens = async () => {
    if (window.confirm('Are you sure you want to clear OAuth state tokens? This is only needed if you are experiencing authentication issues.')) {
      try {
        const { data } = await clearStateTokens();
        alert(`State tokens cleared! ${data.message}`);
      } catch (error) {
        console.error('Error clearing state tokens:', error);
        alert(`Error clearing state tokens: ${error.response?.data?.message || error.message}`);
      }
    }
  };

  // Add this function to handle service restart
  const handleRestartService = async () => {
    try {
      console.log("Restarting Gmail service...");
      setAuthStatus(prev => ({ ...prev, loading: true }));
      await restartService();
      alert('Gmail service restarted successfully!');
      // Refresh auth status
      await fetchAuthStatus();
    } catch (error) {
      console.error('Error restarting service:', error);
      alert(`Failed to restart service: ${error.response?.data?.message || error.message}`);
      setAuthStatus(prev => ({ ...prev, loading: false }));
    }
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
                
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Button
                    variant="outlined"
                    color="error"
                    startIcon={<RefreshIcon />}
                    onClick={handleResetAuth}
                    size="small"
                  >
                    Sign out
                  </Button>
                  
                  <Button
                    variant="outlined"
                    color="primary"
                    startIcon={<PlayArrowIcon />}
                    onClick={handleRestartService}
                    size="small"
                  >
                    Restart Service
                  </Button>
                </Box>
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
                
                <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                  <Button 
                    variant="text"
                    size="small"
                    onClick={fetchAuthStatus}
                  >
                    Refresh Status
                  </Button>
                  
                  {authStatus.token_exists && (
                    <Button
                      variant="text"
                      color="primary"
                      size="small"
                      startIcon={<PlayArrowIcon />}
                      onClick={handleRestartService}
                    >
                      Restart Service
                    </Button>
                  )}
                </Box>
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
          Advanced Settings
        </Typography>
        <Divider sx={{ mb: 2 }} />
        
        <Alert severity="warning" sx={{ mb: 2 }}>
          <AlertTitle>Caution</AlertTitle>
          The following actions are for troubleshooting purposes. Only use them if you're experiencing issues with authentication.
        </Alert>
        
        <Button
          variant="outlined"
          color="error"
          startIcon={<DeleteIcon />}
          onClick={handleClearStateTokens}
          sx={{ mr: 2 }}
        >
          Clear OAuth State Tokens
        </Button>
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
              defaultValue="http://localhost:5173/auth/callback"
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