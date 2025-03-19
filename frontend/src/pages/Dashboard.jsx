import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Card,
  CardContent,
  CardActionArea,
  Button,
  Alert,
  AlertTitle,
  CircularProgress,
} from '@mui/material';
import {
  Webhook as WebhookIcon,
  Email as EmailIcon,
  Check as CheckIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { getHealth, getWebhooks, getEmailConfigs } from '../services/api';

function StatusCard({ title, value, icon, color }) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Grid container spacing={2} alignItems="center">
          <Grid item>
            <Box
              sx={{
                p: 1.5,
                borderRadius: 2,
                bgcolor: `${color}.light`,
                color: `${color}.dark`,
                display: 'flex',
              }}
            >
              {icon}
            </Box>
          </Grid>
          <Grid item xs>
            <Typography variant="h6" component="div">
              {title}
            </Typography>
            <Typography variant="h4" color="text.secondary">
              {value}
            </Typography>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}

function Dashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [health, setHealth] = useState({});
  const [webhooks, setWebhooks] = useState([]);
  const [emailConfigs, setEmailConfigs] = useState([]);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        
        // Get health status
        const healthRes = await getHealth();
        setHealth(healthRes.data);
        
        // Get webhooks
        const webhooksRes = await getWebhooks();
        setWebhooks(webhooksRes.data);
        
        // Get email configs
        const emailConfigsRes = await getEmailConfigs();
        setEmailConfigs(emailConfigsRes.data);
        
        setError(null);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const activeWebhooks = webhooks.filter(webhook => webhook.active).length;
  const activeEmailConfigs = emailConfigs.filter(config => config.active).length;

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', pt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          <AlertTitle>Error</AlertTitle>
          {error}
        </Alert>
      )}
      
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          System Status
        </Typography>
        <Grid container spacing={2} alignItems="center">
          <Grid item>
            {health.email_processor_active ? (
              <CheckIcon color="success" />
            ) : (
              <ErrorIcon color="error" />
            )}
          </Grid>
          <Grid item xs>
            <Typography>
              Email Processor: {health.email_processor_active ? 'Active' : 'Inactive'}
            </Typography>
          </Grid>
          <Grid item>
            <Typography variant="body2" color="text.secondary">
              Version: {health.version || 'Unknown'}
            </Typography>
          </Grid>
        </Grid>
      </Paper>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <StatusCard
            title="Active Webhooks"
            value={activeWebhooks}
            icon={<WebhookIcon />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <StatusCard
            title="Email Configs"
            value={activeEmailConfigs}
            icon={<EmailIcon />}
            color="secondary"
          />
        </Grid>
      </Grid>
      
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardActionArea onClick={() => navigate('/webhooks')}>
              <CardContent>
                <Typography gutterBottom variant="h5" component="div">
                  Manage Webhooks
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Configure webhook endpoints to forward email content
                </Typography>
              </CardContent>
            </CardActionArea>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardActionArea onClick={() => navigate('/email-configs')}>
              <CardContent>
                <Typography gutterBottom variant="h5" component="div">
                  Email Monitoring
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Configure which emails to monitor and forward
                </Typography>
              </CardContent>
            </CardActionArea>
          </Card>
        </Grid>
      </Grid>
      
      {!health.email_processor_active && (
        <Alert severity="warning" sx={{ mt: 3 }}>
          <AlertTitle>Email processor is not active</AlertTitle>
          The email processor is not running. This might be due to missing Gmail API credentials or authorization issues.
          <Box sx={{ mt: 2 }}>
            <Button variant="outlined" color="inherit" onClick={() => navigate('/settings')}>
              Go to Settings
            </Button>
          </Box>
        </Alert>
      )}
    </Box>
  );
}

export default Dashboard; 