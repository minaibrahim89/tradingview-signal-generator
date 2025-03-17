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
} from '@mui/material';
import {
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import { getProcessedEmails } from '../services/api';

function ProcessedEmails() {
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [totalEmails, setTotalEmails] = useState(0);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);

  useEffect(() => {
    fetchEmails();
  }, [page, rowsPerPage]);

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

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Processed Emails
      </Typography>
      
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
    </Box>
  );
}

export default ProcessedEmails; 