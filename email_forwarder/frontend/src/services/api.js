import axios from 'axios';

const API_BASE_URL = '/api/v1';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Webhooks API
export const getWebhooks = () => api.get('/webhooks');
export const getWebhook = (id) => api.get(`/webhooks/${id}`);
export const createWebhook = (data) => api.post('/webhooks', data);
export const updateWebhook = (id, data) => api.put(`/webhooks/${id}`, data);
export const deleteWebhook = (id) => api.delete(`/webhooks/${id}`);

// Email Configs API
export const getEmailConfigs = () => api.get('/email-configs');
export const getEmailConfig = (id) => api.get(`/email-configs/${id}`);
export const createEmailConfig = (data) => api.post('/email-configs', data);
export const updateEmailConfig = (id, data) => api.put(`/email-configs/${id}`, data);
export const deleteEmailConfig = (id) => api.delete(`/email-configs/${id}`);

// Processed Emails API
export const getProcessedEmails = (params) => api.get('/processed-emails', { params });

// Health API
export const getHealth = () => api.get('/health');

export default api; 