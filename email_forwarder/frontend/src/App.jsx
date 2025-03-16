import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box } from '@mui/material';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Webhooks from './pages/Webhooks';
import EmailConfigs from './pages/EmailConfigs';
import ProcessedEmails from './pages/ProcessedEmails';
import Settings from './pages/Settings';

function App() {
  return (
    <Box sx={{ display: 'flex' }}>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="webhooks" element={<Webhooks />} />
          <Route path="email-configs" element={<EmailConfigs />} />
          <Route path="processed-emails" element={<ProcessedEmails />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </Box>
  );
}

export default App; 