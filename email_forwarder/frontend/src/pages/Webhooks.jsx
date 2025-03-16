import React, { useState, useEffect } from 'react';
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
  Button,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Switch,
  FormControlLabel,
  CircularProgress,
  Alert,
  Snackbar,
  Tooltip,
  Divider,
  Card,
  CardContent,
  Collapse,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Send as SendIcon,
  Check as CheckIcon,
  Error as ErrorIcon,
  Code as CodeIcon,
} from '@mui/icons-material';
import { getWebhooks, createWebhook, updateWebhook, deleteWebhook, testWebhook } from '../services/api';

function Webhooks() {
  const [webhooks, setWebhooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingWebhook, setEditingWebhook] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    active: true,
  });
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success',
  });
  const [testResults, setTestResults] = useState(null);
  const [testLoading, setTestLoading] = useState(false);
  const [testingWebhookId, setTestingWebhookId] = useState(null);
  const [showPayload, setShowPayload] = useState(false);

  // Fetch webhooks on component mount
  useEffect(() => {
    fetchWebhooks();
  }, []);

  const fetchWebhooks = async () => {
    try {
      setLoading(true);
      const res = await getWebhooks();
      setWebhooks(res.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching webhooks:', err);
      setError('Failed to load webhooks. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (webhook = null) => {
    if (webhook) {
      setEditingWebhook(webhook);
      setFormData({
        name: webhook.name,
        url: webhook.url,
        active: webhook.active,
      });
    } else {
      setEditingWebhook(null);
      setFormData({
        name: '',
        url: '',
        active: true,
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
  };

  const handleInputChange = (e) => {
    const { name, value, checked } = e.target;
    setFormData({
      ...formData,
      [name]: name === 'active' ? checked : value,
    });
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      
      if (editingWebhook) {
        // Update existing webhook
        await updateWebhook(editingWebhook.id, formData);
        setSnackbar({
          open: true,
          message: 'Webhook updated successfully!',
          severity: 'success',
        });
      } else {
        // Create new webhook
        await createWebhook(formData);
        setSnackbar({
          open: true,
          message: 'Webhook created successfully!',
          severity: 'success',
        });
      }
      
      // Refresh the webhooks list
      await fetchWebhooks();
      handleCloseDialog();
    } catch (err) {
      console.error('Error saving webhook:', err);
      setSnackbar({
        open: true,
        message: `Failed to ${editingWebhook ? 'update' : 'create'} webhook: ${err.message}`,
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this webhook?')) {
      return;
    }
    
    try {
      setLoading(true);
      await deleteWebhook(id);
      await fetchWebhooks();
      setSnackbar({
        open: true,
        message: 'Webhook deleted successfully!',
        severity: 'success',
      });
    } catch (err) {
      console.error('Error deleting webhook:', err);
      setSnackbar({
        open: true,
        message: `Failed to delete webhook: ${err.message}`,
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  const handleTest = async (webhook) => {
    try {
      setTestLoading(true);
      setTestingWebhookId(webhook.id);
      setTestResults(null);
      
      const response = await testWebhook(webhook.id);
      
      setTestResults(response.data);
      
      setSnackbar({
        open: true,
        message: response.data.success ? 
          `Successfully sent test email to webhook ${webhook.name}` : 
          `Failed to send test email to webhook ${webhook.name}`,
        severity: response.data.success ? 'success' : 'error',
      });
    } catch (err) {
      console.error('Error testing webhook:', err);
      setSnackbar({
        open: true,
        message: `Error testing webhook: ${err.response?.data?.detail || err.message}`,
        severity: 'error',
      });
    } finally {
      setTestLoading(false);
      setTestingWebhookId(null);
    }
  };

  const handleTogglePayload = () => {
    setShowPayload(!showPayload);
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
        <Typography variant="h4">Webhooks</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Add Webhook
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {testResults && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="h6">
                Test Results: {testResults.webhook_name}
              </Typography>
              <Box>
                {testResults.success ? (
                  <Tooltip title="Success">
                    <CheckIcon color="success" />
                  </Tooltip>
                ) : (
                  <Tooltip title="Failed">
                    <ErrorIcon color="error" />
                  </Tooltip>
                )}
              </Box>
            </Box>
            
            <Divider sx={{ my: 1 }} />
            
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Status Code: {testResults.status_code || 'N/A'}
            </Typography>
            
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Response: {testResults.response || 'No response'}
            </Typography>
            
            <Button 
              startIcon={<CodeIcon />}
              size="small"
              onClick={handleTogglePayload}
              sx={{ mt: 1 }}
            >
              {showPayload ? 'Hide' : 'Show'} Sample Payload
            </Button>
            
            <Collapse in={showPayload}>
              <Paper 
                sx={{ 
                  p: 2, 
                  mt: 1, 
                  bgcolor: 'grey.100',
                  maxHeight: '200px',
                  overflow: 'auto'
                }}
              >
                <pre>{testResults.sample_payload}</pre>
              </Paper>
            </Collapse>
          </CardContent>
        </Card>
      )}

      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>URL</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading && webhooks.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} align="center" sx={{ py: 3 }}>
                    <CircularProgress size={24} />
                  </TableCell>
                </TableRow>
              ) : webhooks.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} align="center" sx={{ py: 3 }}>
                    <Typography color="text.secondary">
                      No webhooks configured yet. Click "Add Webhook" to create one.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                webhooks.map((webhook) => (
                  <TableRow key={webhook.id}>
                    <TableCell>{webhook.name}</TableCell>
                    <TableCell sx={{ wordBreak: 'break-all' }}>{webhook.url}</TableCell>
                    <TableCell>
                      <Typography
                        sx={{
                          color: webhook.active ? 'success.main' : 'text.disabled',
                          fontWeight: 'medium',
                        }}
                      >
                        {webhook.active ? 'Active' : 'Inactive'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Tooltip title="Test Webhook">
                        <IconButton
                          color="info"
                          onClick={() => handleTest(webhook)}
                          disabled={loading || (testLoading && testingWebhookId === webhook.id)}
                        >
                          {testLoading && testingWebhookId === webhook.id ? 
                            <CircularProgress size={24} /> : 
                            <SendIcon />
                          }
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Edit">
                        <IconButton
                          color="primary"
                          onClick={() => handleOpenDialog(webhook)}
                          disabled={loading}
                        >
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton
                          color="error"
                          onClick={() => handleDelete(webhook.id)}
                          disabled={loading}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Webhook Form Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingWebhook ? 'Edit Webhook' : 'Add Webhook'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            name="name"
            label="Webhook Name"
            type="text"
            fullWidth
            variant="outlined"
            value={formData.name}
            onChange={handleInputChange}
            required
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            name="url"
            label="Webhook URL"
            type="url"
            fullWidth
            variant="outlined"
            value={formData.url}
            onChange={handleInputChange}
            required
            helperText="The URL that will receive webhook data"
            sx={{ mb: 2 }}
          />
          <FormControlLabel
            control={
              <Switch
                checked={formData.active}
                onChange={handleInputChange}
                name="active"
              />
            }
            label="Active"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {loading ? <CircularProgress size={24} /> : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Webhooks; 