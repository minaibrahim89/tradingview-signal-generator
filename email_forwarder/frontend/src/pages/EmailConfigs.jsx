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
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { getEmailConfigs, createEmailConfig, updateEmailConfig, deleteEmailConfig } from '../services/api';

function EmailConfigs() {
  const [emailConfigs, setEmailConfigs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingConfig, setEditingConfig] = useState(null);
  const [formData, setFormData] = useState({
    email_address: '',
    filter_subject: '',
    filter_sender: '',
    check_interval_seconds: 60,
    active: true,
  });
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success',
  });

  // Fetch email configs on component mount
  useEffect(() => {
    fetchEmailConfigs();
  }, []);

  const fetchEmailConfigs = async () => {
    try {
      setLoading(true);
      const res = await getEmailConfigs();
      setEmailConfigs(res.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching email configurations:', err);
      setError('Failed to load email configurations. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (config = null) => {
    if (config) {
      setEditingConfig(config);
      setFormData({
        email_address: config.email_address,
        filter_subject: config.filter_subject || '',
        filter_sender: config.filter_sender || '',
        check_interval_seconds: config.check_interval_seconds,
        active: config.active,
      });
    } else {
      setEditingConfig(null);
      setFormData({
        email_address: '',
        filter_subject: '',
        filter_sender: '',
        check_interval_seconds: 60,
        active: true,
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
  };

  const handleInputChange = (e) => {
    const { name, value, checked, type } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' 
        ? checked 
        : type === 'number'
          ? parseInt(value, 10)
          : value,
    });
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      
      if (editingConfig) {
        // Update existing email config
        await updateEmailConfig(editingConfig.id, formData);
        setSnackbar({
          open: true,
          message: 'Email configuration updated successfully!',
          severity: 'success',
        });
      } else {
        // Create new email config
        await createEmailConfig(formData);
        setSnackbar({
          open: true,
          message: 'Email configuration created successfully!',
          severity: 'success',
        });
      }
      
      // Refresh the email configs list
      await fetchEmailConfigs();
      handleCloseDialog();
    } catch (err) {
      console.error('Error saving email configuration:', err);
      setSnackbar({
        open: true,
        message: `Failed to ${editingConfig ? 'update' : 'create'} email configuration: ${err.message}`,
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this email configuration?')) {
      return;
    }
    
    try {
      setLoading(true);
      await deleteEmailConfig(id);
      await fetchEmailConfigs();
      setSnackbar({
        open: true,
        message: 'Email configuration deleted successfully!',
        severity: 'success',
      });
    } catch (err) {
      console.error('Error deleting email configuration:', err);
      setSnackbar({
        open: true,
        message: `Failed to delete email configuration: ${err.message}`,
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
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
        <Typography variant="h4">Email Monitoring</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Add Configuration
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Email Address</TableCell>
                <TableCell>Filters</TableCell>
                <TableCell>Check Interval</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading && emailConfigs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center" sx={{ py: 3 }}>
                    <CircularProgress size={24} />
                  </TableCell>
                </TableRow>
              ) : emailConfigs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center" sx={{ py: 3 }}>
                    <Typography color="text.secondary">
                      No email monitoring configurations yet. Click "Add Configuration" to create one.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                emailConfigs.map((config) => (
                  <TableRow key={config.id}>
                    <TableCell>{config.email_address}</TableCell>
                    <TableCell>
                      {config.filter_subject && (
                        <Typography variant="body2">
                          Subject: {config.filter_subject}
                        </Typography>
                      )}
                      {config.filter_sender && (
                        <Typography variant="body2">
                          Sender: {config.filter_sender}
                        </Typography>
                      )}
                      {!config.filter_subject && !config.filter_sender && (
                        <Typography variant="body2" color="text.secondary">
                          No filters
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>{config.check_interval_seconds} seconds</TableCell>
                    <TableCell>
                      <Typography
                        sx={{
                          color: config.active ? 'success.main' : 'text.disabled',
                          fontWeight: 'medium',
                        }}
                      >
                        {config.active ? 'Active' : 'Inactive'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <IconButton
                        color="primary"
                        onClick={() => handleOpenDialog(config)}
                        disabled={loading}
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        color="error"
                        onClick={() => handleDelete(config.id)}
                        disabled={loading}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Add/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingConfig ? 'Edit Email Configuration' : 'Add Email Configuration'}
        </DialogTitle>
        <DialogContent>
          <Box component="form" sx={{ mt: 1 }}>
            <TextField
              margin="normal"
              required
              fullWidth
              label="Email Address to Monitor"
              name="email_address"
              type="email"
              value={formData.email_address}
              onChange={handleInputChange}
              autoFocus
              helperText="The Gmail address to monitor for new emails"
            />
            <TextField
              margin="normal"
              fullWidth
              label="Filter by Subject (Optional)"
              name="filter_subject"
              value={formData.filter_subject}
              onChange={handleInputChange}
              helperText="Only forward emails containing this text in the subject (case-insensitive)"
            />
            <TextField
              margin="normal"
              fullWidth
              label="Filter by Sender (Optional)"
              name="filter_sender"
              value={formData.filter_sender}
              onChange={handleInputChange}
              helperText="Only forward emails from this sender"
            />
            <TextField
              margin="normal"
              required
              fullWidth
              label="Check Interval (seconds)"
              name="check_interval_seconds"
              type="number"
              value={formData.check_interval_seconds}
              onChange={handleInputChange}
              inputProps={{ min: 30 }}
              helperText="How often to check for new emails (minimum 30 seconds)"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={formData.active}
                  onChange={handleInputChange}
                  name="active"
                  color="primary"
                />
              }
              label="Active"
              sx={{ mt: 1 }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog} disabled={loading}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={
              loading || 
              !formData.email_address || 
              formData.check_interval_seconds < 30
            }
          >
            {loading ? <CircularProgress size={24} /> : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default EmailConfigs; 