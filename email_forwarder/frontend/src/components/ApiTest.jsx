import React, { useState } from 'react';
import { Box, Typography, Paper, Button, Alert, CircularProgress, Divider, Accordion, AccordionSummary, AccordionDetails } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import axios from 'axios';
import apiDebug from '../services/apiDebug';

function ApiTest() {
  const [apiStatus, setApiStatus] = useState({
    loading: false,
    success: null,
    error: null,
    data: null,
  });

  const [diagnosticResults, setDiagnosticResults] = useState(null);

  const testBackendConnection = async () => {
    setApiStatus({ loading: true, success: null, error: null, data: null });
    
    try {
      // Test direct connection to the API test endpoint
      const response = await axios.get('/api/test');
      console.log('API test response:', response);
      setApiStatus({
        loading: false,
        success: true,
        error: null,
        data: response.data,
      });
    } catch (error) {
      console.error('API test error:', error);
      setApiStatus({
        loading: false,
        success: false,
        error: error.message || 'Failed to connect to API',
        data: null,
      });
    }
  };

  const testHealthEndpoint = async () => {
    setApiStatus({ loading: true, success: null, error: null, data: null });
    
    try {
      // Test connection to the health endpoint
      const response = await axios.get('/health');
      console.log('Health endpoint response:', response);
      setApiStatus({
        loading: false,
        success: true,
        error: null,
        data: response.data,
      });
    } catch (error) {
      console.error('Health endpoint error:', error);
      setApiStatus({
        loading: false,
        success: false,
        error: error.message || 'Failed to connect to health endpoint',
        data: null,
      });
    }
  };

  const testV1Api = async () => {
    setApiStatus({ loading: true, success: null, error: null, data: null });
    
    try {
      // Test connection to the v1 API through our API service
      const response = await axios.get('/api/v1/auth/status');
      console.log('API v1 response:', response);
      setApiStatus({
        loading: false,
        success: true,
        error: null,
        data: response.data,
      });
    } catch (error) {
      console.error('API v1 error:', error);
      setApiStatus({
        loading: false,
        success: false,
        error: error.message || 'Failed to connect to API v1',
        data: null,
      });
    }
  };

  const runFullDiagnostics = async () => {
    setApiStatus({ loading: true, success: null, error: null, data: null });
    
    try {
      // Get CORS info for debugging
      apiDebug.getCorsInfo();
      
      // Check network conditions
      await apiDebug.checkNetworkConditions();
      
      // Run full API diagnostics
      const results = await apiDebug.runApiDiagnostics();
      setDiagnosticResults(results);
      
      setApiStatus({
        loading: false,
        success: results.summary.successful > 0,
        error: results.summary.failed > 0 ? `${results.summary.failed} endpoints failed` : null,
        data: { message: "Diagnostic complete. See console and results below." }
      });
    } catch (error) {
      console.error('Diagnostics error:', error);
      setApiStatus({
        loading: false,
        success: false,
        error: error.message || 'Failed to run diagnostics',
        data: null,
      });
    }
  };

  return (
    <Paper sx={{ p: 3, mt: 3 }}>
      <Typography variant="h6" gutterBottom>
        API Connectivity Test
      </Typography>
      
      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
        <Button 
          variant="contained" 
          onClick={testBackendConnection}
          disabled={apiStatus.loading}
        >
          Test API Endpoint
        </Button>
        
        <Button 
          variant="contained" 
          onClick={testHealthEndpoint}
          disabled={apiStatus.loading}
        >
          Test Health Endpoint
        </Button>
        
        <Button 
          variant="contained" 
          onClick={testV1Api}
          disabled={apiStatus.loading}
        >
          Test V1 API
        </Button>

        <Button 
          variant="contained" 
          color="primary"
          onClick={runFullDiagnostics}
          disabled={apiStatus.loading}
        >
          Run Full Diagnostics
        </Button>
      </Box>
      
      {apiStatus.loading && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <CircularProgress size={24} />
          <Typography>Testing API connection...</Typography>
        </Box>
      )}
      
      {apiStatus.success === true && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Successfully connected to API!
        </Alert>
      )}
      
      {apiStatus.success === false && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to connect to API: {apiStatus.error}
        </Alert>
      )}
      
      {apiStatus.data && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle1" gutterBottom>
            Response Data:
          </Typography>
          <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
            <pre style={{ margin: 0, overflow: 'auto' }}>
              {JSON.stringify(apiStatus.data, null, 2)}
            </pre>
          </Paper>
        </Box>
      )}

      {diagnosticResults && (
        <Box sx={{ mt: 3 }}>
          <Divider sx={{ my: 2 }} />
          <Typography variant="h6" gutterBottom>
            Diagnostic Results
          </Typography>
          
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle1">Summary:</Typography>
            <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
              <pre style={{ margin: 0, overflow: 'auto' }}>
                {JSON.stringify(diagnosticResults.summary, null, 2)}
              </pre>
            </Paper>
          </Box>
          
          <Typography variant="subtitle1">Detailed Results:</Typography>
          {Object.keys(diagnosticResults.results.details).map((endpoint) => (
            <Accordion key={endpoint} sx={{ mb: 1 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography>
                  {endpoint} - {diagnosticResults.results.success.includes(endpoint) ? 
                    '✅ Success' : '❌ Failed'}
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
                  <pre style={{ margin: 0, overflow: 'auto' }}>
                    {JSON.stringify(diagnosticResults.results.details[endpoint], null, 2)}
                  </pre>
                </Paper>
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>
      )}
      
      <Box sx={{ mt: 4 }}>
        <Typography variant="subtitle1" gutterBottom>
          Troubleshooting Steps:
        </Typography>
        <ol>
          <li>Ensure both frontend and backend are running</li>
          <li>Check network console for CORS errors</li>
          <li>Verify the proxy configuration in vite.config.js</li>
          <li>Make sure the backend is running on the expected port (8000)</li>
          <li>Check that the API endpoints are correctly defined</li>
          <li>Review browser console for any errors</li>
          <li>Check server logs for any backend errors</li>
        </ol>
      </Box>
    </Paper>
  );
}

export default ApiTest;