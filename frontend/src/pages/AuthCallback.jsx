import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Box, CircularProgress, Typography, Alert, Button } from '@mui/material';
import axios from 'axios';

function AuthCallback() {
  const navigate = useNavigate();
  const location = useLocation();
  const [status, setStatus] = useState('processing');
  const [error, setError] = useState(null);
  const [isAuthExpired, setIsAuthExpired] = useState(false);

  const handleTryAgain = () => {
    // Redirect to the login endpoint to start a new authentication flow
    window.location.href = '/api/v1/auth/login';
  };

  useEffect(() => {
    const handleCallback = async () => {
      try {
        console.log("AuthCallback: Processing callback");
        
        // Get the query parameters from the URL
        const queryParams = new URLSearchParams(location.search);
        const code = queryParams.get('code');
        const state = queryParams.get('state');
        const errorParam = queryParams.get('error');
        
        console.log("AuthCallback params:", { 
          code: code ? code.substring(0, 5) + "..." : "missing", 
          state: state ? state.substring(0, 5) + "..." : "missing",
          error: errorParam || "none"
        });
        
        if (errorParam) {
          setStatus('error');
          setError(`Google returned an error: ${errorParam}`);
          return;
        }
        
        if (!code) {
          setStatus('error');
          setError('No authorization code received from Google');
          return;
        }

        if (!state) {
          console.warn("No state parameter received, but continuing anyway");
        }

        // Short delay to ensure backend has processed state tokens
        console.log("Adding short delay before API call...");
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Send the code to the backend
        console.log("Sending code to backend...");
        const response = await axios.get(`/api/v1/auth/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`, {
          headers: {
            'Accept': 'application/json'
          }
        });
        
        console.log("Backend response:", response.data);
        
        // If successful, set status to success and redirect to settings
        setStatus('success');
        setTimeout(() => {
          navigate('/settings');
        }, 1500);
      } catch (error) {
        console.error('Error processing auth callback:', error);
        
        let errorMessage = 'Failed to process authentication';
        if (error.response) {
          console.error('Error response:', error.response.data);
          errorMessage = error.response.data.message || errorMessage;
          
          // Check if this is an expired/invalid authorization code
          if (errorMessage.includes('authorization code has expired') || 
              errorMessage.includes('invalid_grant')) {
            setIsAuthExpired(true);
          }
        }
        
        setStatus('error');
        setError(errorMessage);
      }
    };

    handleCallback();
  }, [location, navigate]);

  return (
    <Box sx={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center', 
      justifyContent: 'center', 
      height: '70vh' 
    }}>
      {status === 'processing' && (
        <>
          <CircularProgress size={60} sx={{ mb: 3 }} />
          <Typography variant="h6">
            Completing authentication...
          </Typography>
        </>
      )}
      
      {status === 'success' && (
        <Alert severity="success" sx={{ mt: 2 }}>
          Successfully authenticated! Redirecting...
        </Alert>
      )}
      
      {status === 'error' && (
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
          <Alert severity="error" sx={{ mt: 2 }}>
            {error || 'An error occurred during authentication'}
          </Alert>
          
          {isAuthExpired && (
            <Button 
              variant="contained" 
              color="primary" 
              onClick={handleTryAgain}
              sx={{ mt: 2 }}
            >
              Try Again
            </Button>
          )}
        </Box>
      )}
    </Box>
  );
}

export default AuthCallback;
