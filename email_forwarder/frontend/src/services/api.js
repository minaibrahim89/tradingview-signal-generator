import axios from 'axios';

// Determine the base URL for API calls
// In development, Vite's proxy will handle routing to the backend
const BASE_URL = '/api/v1';

const api = axios.create({
    baseURL: BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add request interceptor for debugging
api.interceptors.request.use(
    (config) => {
        console.log(`Making ${config.method.toUpperCase()} request to: ${config.baseURL}${config.url}`);
        return config;
    },
    (error) => {
        console.error('Request error:', error);
        return Promise.reject(error);
    }
);

// Add response interceptor for debugging
api.interceptors.response.use(
    (response) => {
        console.log(`Received response from ${response.config.url}:`, response.status);
        return response;
    },
    (error) => {
        console.error('Response error:', error.response || error);
        return Promise.reject(error);
    }
);

// Auth API
export const getAuthStatus = () => api.get('/auth/status/');
export const uploadCredentials = (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/auth/upload-credentials/', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
};
export const resetAuth = () => api.post('/auth/reset-auth/');

// Webhooks API
export const getWebhooks = () => api.get('/webhooks/');
export const getWebhook = (id) => api.get(`/webhooks/${id}/`);
export const createWebhook = (data) => api.post('/webhooks/', data);
export const updateWebhook = (id, data) => api.put(`/webhooks/${id}/`, data);
export const deleteWebhook = (id) => api.delete(`/webhooks/${id}/`);

// Email Configs API
export const getEmailConfigs = () => api.get('/email-configs/');
export const getEmailConfig = (id) => api.get(`/email-configs/${id}/`);
export const createEmailConfig = (data) => api.post('/email-configs/', data);
export const updateEmailConfig = (id, data) => api.put(`/email-configs/${id}/`, data);
export const deleteEmailConfig = (id) => api.delete(`/email-configs/${id}/`);

// Stats API
export const getDashboardStats = () => api.get('/stats/dashboard/');
export const getEmailsSummary = () => api.get('/stats/processed-emails/summary/');

// Processed Emails API
export const getProcessedEmails = (params) => api.get('/processed-emails/', { params });
export const getProcessedEmail = (id) => api.get(`/processed-emails/${id}/`);
export const deleteProcessedEmail = (id) => api.delete(`/processed-emails/${id}/`);

// Health API
export const getHealth = () => axios.get('/health');

export default api; 