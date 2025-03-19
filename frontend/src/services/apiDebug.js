import axios from 'axios';

// Configuration
const ENDPOINTS = [
    { name: 'Health Check', url: '/health', method: 'get' },
    { name: 'API Test', url: '/api/test', method: 'get' },
    { name: 'Auth Status', url: '/api/v1/auth/status', method: 'get' },
    { name: 'Dashboard Stats', url: '/api/v1/stats/dashboard', method: 'get' },
    { name: 'List Webhooks', url: '/api/v1/webhooks', method: 'get' },
    { name: 'List Email Configs', url: '/api/v1/email-configs', method: 'get' },
];

// Main diagnostic function
export const runApiDiagnostics = async () => {
    console.group('🔍 API Connection Diagnostics');
    console.log('Starting API diagnostics...');

    const results = {
        success: [],
        failure: [],
        details: {}
    };

    // Test each endpoint
    for (const endpoint of ENDPOINTS) {
        try {
            console.log(`Testing ${endpoint.name}: ${endpoint.method.toUpperCase()} ${endpoint.url}`);
            const startTime = performance.now();
            const response = await axios({
                method: endpoint.method,
                url: endpoint.url,
                timeout: 5000 // 5 seconds timeout
            });
            const duration = (performance.now() - startTime).toFixed(2);

            results.success.push(endpoint.name);
            results.details[endpoint.name] = {
                status: response.status,
                statusText: response.statusText,
                duration: `${duration}ms`,
                dataPreview: truncateData(response.data),
                headers: response.headers,
            };

            console.log(`✅ ${endpoint.name}: Success (${duration}ms)`);
        } catch (error) {
            results.failure.push(endpoint.name);
            results.details[endpoint.name] = {
                error: error.message,
                status: error.response?.status,
                statusText: error.response?.statusText,
                data: error.response?.data,
                request: {
                    url: endpoint.url,
                    method: endpoint.method,
                }
            };

            console.error(`❌ ${endpoint.name}: Failed`, error);
        }
    }

    // Network information
    const connectionInfo = {
        online: navigator.onLine,
        userAgent: navigator.userAgent,
        location: window.location.href,
    };

    // Summary
    const summary = {
        totalEndpoints: ENDPOINTS.length,
        successful: results.success.length,
        failed: results.failure.length,
        successRate: `${Math.round((results.success.length / ENDPOINTS.length) * 100)}%`,
        connectionInfo
    };

    console.log('📊 Diagnostics Summary:', summary);
    console.log('👍 Successful endpoints:', results.success);
    console.log('👎 Failed endpoints:', results.failure);
    console.groupEnd();

    return {
        summary,
        results
    };
};

// Helper to truncate large data objects for logging
function truncateData(data, maxLength = 200) {
    if (!data) return null;

    try {
        const str = JSON.stringify(data);
        if (str.length <= maxLength) return data;

        return {
            truncated: true,
            preview: `${str.substring(0, maxLength)}...`,
            fullLength: str.length
        };
    } catch (e) {
        return {
            type: typeof data,
            toString: String(data).substring(0, maxLength)
        };
    }
}

// Gets detailed CORS debugging info
export const getCorsInfo = () => {
    const headers = {
        'Standard CORS headers': [
            'Access-Control-Allow-Origin',
            'Access-Control-Allow-Methods',
            'Access-Control-Allow-Headers',
            'Access-Control-Allow-Credentials',
            'Access-Control-Max-Age',
            'Access-Control-Expose-Headers'
        ],
        'Request headers sent automatically': [
            'Origin',
            'Referer',
            'User-Agent',
            'Host'
        ]
    };

    console.log('🔍 CORS Debugging Info:');
    console.log('Current origin:', window.location.origin);
    console.log('Headers to check in network responses:', headers);

    return {
        origin: window.location.origin,
        headers
    };
};

// Check browser network conditions
export const checkNetworkConditions = async () => {
    try {
        const connection = navigator.connection ||
            navigator.mozConnection ||
            navigator.webkitConnection;

        const conditions = {
            online: navigator.onLine,
            connectionInfo: connection ? {
                type: connection.type,
                effectiveType: connection.effectiveType,
                downlinkMax: connection.downlinkMax,
                rtt: connection.rtt,
                saveData: connection.saveData
            } : 'Not available'
        };

        console.log('📡 Network conditions:', conditions);
        return conditions;
    } catch (error) {
        console.error('Error checking network conditions:', error);
        return { error: error.message };
    }
};

export default {
    runApiDiagnostics,
    getCorsInfo,
    checkNetworkConditions
}; 