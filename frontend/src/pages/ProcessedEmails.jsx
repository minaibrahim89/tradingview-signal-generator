import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  CircularProgress,
  Alert,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Snackbar,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Visibility as ViewIcon,
  DeleteSweep as DeleteSweepIcon,
  Sync as SyncIcon,
} from '@mui/icons-material';
import { getProcessedEmails, clearAllProcessedEmails } from '../services/api';

function ProcessedEmails() {
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [totalEmails, setTotalEmails] = useState(0);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [openConfirmDialog, setOpenConfirmDialog] = useState(false);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success',
  });
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  
  // WebSocket reference
  const wsRef = useRef(null);

  useEffect(() => {
    fetchEmails();
    
    // Setup WebSocket connection for real-time updates
    connectWebSocket();
    
    // Cleanup function to close WebSocket on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      
      // Clear polling interval if it exists
      if (window.emailPollingInterval) {
        clearInterval(window.emailPollingInterval);
        window.emailPollingInterval = null;
      }
    };
  }, [page, rowsPerPage]);
  
  const connectWebSocket = () => {
    // Close existing connection if any
    if (wsRef.current) {
      wsRef.current.close();
    }
    
    // Define URLs to try in order (fallback mechanism)
    const wsUrls = [
      `ws://${window.location.hostname}:8000/ws`,                // Root path WebSocket
      `ws://${window.location.hostname}:8000/ws-test`,           // Direct test endpoint
      `ws://${window.location.hostname}:8000/api/v1/ws/emails`,  // Routed endpoint
      'ws://127.0.0.1:8000/ws',                                 // Root with IP
      'ws://127.0.0.1:8000/ws-test',                            // Alternate direct endpoint
      'ws://127.0.0.1:8000/api/v1/ws/emails',                   // Alternate routed endpoint
      'ws://localhost:8000/ws',                                 // Root with localhost
      'ws://localhost:8000/ws-test',                            // Local hostname direct endpoint
      'ws://localhost:8000/api/v1/ws/emails'                    // Local hostname routed endpoint
    ];
    
    // Try to connect to the first URL
    let wsUrlIndex = 0;
    
    const tryConnection = () => {
      if (wsUrlIndex >= wsUrls.length) {
        console.error('❌ All WebSocket connection attempts failed');
        setWsConnected(false);
        setError('Failed to establish WebSocket connection. Using polling fallback instead.');
        
        // Setup polling fallback
        console.log('Setting up polling fallback since WebSocket connection failed');
        const intervalId = setInterval(() => {
          if (autoRefresh) {
            console.log('Polling for new emails');
            fetchEmails();
          } else {
            clearInterval(intervalId);
          }
        }, 30000);
        
        // Store the interval ID for cleanup
        window.emailPollingInterval = intervalId;
        
        return;
      }
      
      const wsUrl = wsUrls[wsUrlIndex];
      console.log(`Connecting to WebSocket endpoint (attempt ${wsUrlIndex + 1}/${wsUrls.length}): ${wsUrl}`);
      
      try {
        const ws = new WebSocket(wsUrl);
        
        // Set connection timeout
        const connectionTimeout = setTimeout(() => {
          console.log(`Connection to ${wsUrl} timed out, trying next endpoint...`);
          ws.close();
          wsUrlIndex++;
          tryConnection();
        }, 5000); // Increase timeout to 5 seconds
        
        ws.onopen = () => {
          // Clear the timeout since we're connected
          clearTimeout(connectionTimeout);
          
          console.log(`✅ WebSocket connection established successfully to ${wsUrl}`);
          wsRef.current = ws;
          setWsConnected(true);
          setError(null);
          
          // Send a ping every 30 seconds to keep connection alive
          const pingInterval = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
              console.log('Sending ping to keep WebSocket alive');
              ws.send(JSON.stringify({ type: 'ping' }));
            } else {
              clearInterval(pingInterval);
            }
          }, 30000);
        };
        
        ws.onmessage = (event) => {
          if (!autoRefresh) return;
          
          console.log('📩 WebSocket message received:', event.data);
          try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'email_processed') {
              // Update last update timestamp
              setLastUpdate(new Date());
              
              // Show notification
              setSnackbar({
                open: true,
                message: `New email processed: ${data.data.subject}`,
                severity: 'info',
              });
              
              console.log('Refreshing emails due to new email notification');
              // Always refresh emails when we get a new email notification
              fetchEmails();
            } else if (data.type === 'pong' || data.type === 'connection_status' || data.type === 'echo') {
              console.log(`Received ${data.type} from server:`, data);
              
              // For the root WebSocket, set up a polling mechanism to fetch emails
              if (wsUrl.endsWith('/ws') || wsUrl.endsWith('/ws-test')) {
                console.log('Connected to basic WebSocket endpoint, setting up polling for emails');
                
                // Clear any existing polling interval
                if (window.emailPollingInterval) {
                  clearInterval(window.emailPollingInterval);
                }
                
                // Set up polling
                window.emailPollingInterval = setInterval(() => {
                  if (autoRefresh) {
                    console.log('Polling for new emails (backup mechanism)');
                    fetchEmails();
                  }
                }, 20000); // Poll every 20 seconds
              }
            }
          } catch (err) {
            console.error('Error processing WebSocket message:', err);
          }
        };
        
        ws.onclose = (event) => {
          clearTimeout(connectionTimeout);
          console.log(`⚠️ WebSocket connection closed with code: ${event.code}, reason: ${event.reason}`);
          setWsConnected(false);
          
          // Try to reconnect after 5 seconds
          setTimeout(() => {
            if (autoRefresh) {
              console.log('Attempting to reconnect WebSocket...');
              connectWebSocket();
            }
          }, 5000);
        };
        
        ws.onerror = (error) => {
          clearTimeout(connectionTimeout);
          console.error('❌ WebSocket error:', error);
          
          // Try next URL
          wsUrlIndex++;
          tryConnection();
        };
      } catch (err) {
        console.error('❌ Error creating WebSocket connection:', err);
        
        // Try next URL
        wsUrlIndex++;
        tryConnection();
      }
    };
    
    // Start trying connections
    tryConnection();
  };

  const fetchEmails = async () => {
    try {
      setLoading(true);
      
      console.log('Fetching emails with params:', { page, page_size: rowsPerPage });
      
      // Use the real API implementation
      const response = await getProcessedEmails({ 
        page,
        page_size: rowsPerPage 
      });
      
      console.log('API Response:', response);
      
      if (response && response.data) {
        const responseData = response.data;
        
        // The backend returns { data: [...], total: number, page: number, page_size: number }
        if (responseData.data && Array.isArray(responseData.data)) {
          setEmails(responseData.data);
          setTotalEmails(responseData.total || 0);
          console.log('Successfully processed emails:', responseData.data.length);
        } else {
          console.error('Response data is not in expected format:', responseData);
          setEmails([]);
          setTotalEmails(0);
        }
      } else {
        console.error('Invalid API response:', response);
        setEmails([]);
        setTotalEmails(0);
      }
      
      setError(null);
    } catch (err) {
      console.error('Error fetching processed emails:', err);
      setError('Failed to load processed emails. Please try again.');
      setEmails([]);
      setTotalEmails(0);
    } finally {
      setLoading(false);
    }
  };

  const handleClearAllEmails = async () => {
    setOpenConfirmDialog(false);
    
    try {
      setLoading(true);
      const response = await clearAllProcessedEmails();
      console.log('Clear all response:', response);
      
      setSnackbar({
        open: true,
        message: response.data?.message || 'Successfully cleared all processed emails',
        severity: 'success',
      });
      
      // Reset to first page and refresh
      setPage(0);
      await fetchEmails();
    } catch (err) {
      console.error('Error clearing emails:', err);
      setSnackbar({
        open: true,
        message: `Failed to clear emails: ${err.response?.data?.detail || err.message}`,
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };
  
  const handleToggleAutoRefresh = (event) => {
    const newValue = event.target.checked;
    setAutoRefresh(newValue);
    
    // If turning on auto-refresh, reconnect WebSocket
    if (newValue && !wsConnected) {
      connectWebSocket();
    }
    
    // If turning off auto-refresh, disconnect WebSocket
    if (!newValue && wsConnected && wsRef.current) {
      wsRef.current.close();
      setWsConnected(false);
    }
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleOpenDialog = (email) => {
    setSelectedEmail(email);
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
  };

  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  return (
    <Box>
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity}>
          {snackbar.message}
        </Alert>
      </Snackbar>
      
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h4">Processed Emails</Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <FormControlLabel
              control={
                <Switch
                  checked={autoRefresh}
                  onChange={handleToggleAutoRefresh}
                  color="primary"
                />
              }
              label="Auto-refresh"
            />
            <Chip 
              size="small"
              icon={<SyncIcon />}
              label={wsConnected ? "Connected" : "Disconnected"} 
              color={wsConnected ? "success" : "error"}
              sx={{ ml: 1 }}
            />
          </Box>
          <Button
            variant="outlined"
            startIcon={<SyncIcon />}
            onClick={fetchEmails}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            color="error"
            startIcon={<DeleteSweepIcon />}
            onClick={() => setOpenConfirmDialog(true)}
            disabled={loading || totalEmails === 0}
          >
            Clear All
          </Button>
        </Box>
      </Box>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {lastUpdate && (
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
          Last updated: {new Date(lastUpdate).toLocaleString()}
        </Typography>
      )}
      
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Subject</TableCell>
                <TableCell>Sender</TableCell>
                <TableCell>Received</TableCell>
                <TableCell>Processed</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading && emails.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 3 }}>
                    <CircularProgress size={24} />
                  </TableCell>
                </TableRow>
              ) : emails.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 3 }}>
                    <Typography color="text.secondary">
                      No processed emails found.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                emails.map((email) => (
                  <TableRow key={email.id}>
                    <TableCell>{email.subject}</TableCell>
                    <TableCell>{email.sender}</TableCell>
                    <TableCell>{formatDate(email.received_at)}</TableCell>
                    <TableCell>{formatDate(email.processed_at)}</TableCell>
                    <TableCell>
                      {email.forwarded_successfully ? (
                        <Chip
                          icon={<SuccessIcon />}
                          label="Forwarded"
                          color="success"
                          size="small"
                        />
                      ) : (
                        <Chip
                          icon={<ErrorIcon />}
                          label="Failed"
                          color="error"
                          size="small"
                        />
                      )}
                    </TableCell>
                    <TableCell>
                      <IconButton
                        color="primary"
                        onClick={() => handleOpenDialog(email)}
                      >
                        <ViewIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={totalEmails}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Paper>
      
      {/* Email details dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        {selectedEmail && (
          <>
            <DialogTitle>Email Details</DialogTitle>
            <DialogContent dividers>
              <Typography variant="subtitle1" gutterBottom>
                <strong>Subject:</strong> {selectedEmail.subject}
              </Typography>
              <Typography variant="subtitle2" gutterBottom>
                <strong>From:</strong> {selectedEmail.sender}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Received:</strong> {formatDate(selectedEmail.received_at)}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Processed:</strong> {formatDate(selectedEmail.processed_at)}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Status:</strong>{' '}
                {selectedEmail.forwarded_successfully ? 'Successfully forwarded' : 'Failed to forward'}
              </Typography>
              
              <Box sx={{ mt: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Content Preview:
                </Typography>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {selectedEmail.body_snippet}
                </Typography>
              </Box>
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseDialog}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>
      
      {/* Confirm clear all dialog */}
      <Dialog
        open={openConfirmDialog}
        onClose={() => setOpenConfirmDialog(false)}
        aria-labelledby="alert-dialog-title"
        aria-describedby="alert-dialog-description"
      >
        <DialogTitle id="alert-dialog-title">
          Clear All Processed Emails?
        </DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete all processed email records? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenConfirmDialog(false)} color="primary">
            Cancel
          </Button>
          <Button onClick={handleClearAllEmails} color="error" autoFocus>
            Clear All
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default ProcessedEmails; 