// Simple Node.js server as a fallback for Azure deployment
const http = require('http');
const fs = require('fs');
const path = require('path');

const port = process.env.PORT || 8000;

const server = http.createServer((req, res) => {
  console.log(`Request received: ${req.method} ${req.url}`);
  
  // Serve static files
  if (req.url === '/' || req.url === '/index.html') {
    try {
      if (fs.existsSync(path.join(__dirname, 'static', 'index.html'))) {
        res.writeHead(200, { 'Content-Type': 'text/html' });
        fs.createReadStream(path.join(__dirname, 'static', 'index.html')).pipe(res);
        return;
      }
    } catch (error) {
      console.error('Error serving index.html:', error);
    }
    
    // Fallback if index.html doesn't exist
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>App Status</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            h1 { color: #333; }
            .card { border: 1px solid #ddd; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
          </style>
        </head>
        <body>
          <h1>Application Status</h1>
          <div class="card">
            <h2>Server is running!</h2>
            <p>This is the Node.js fallback server. The main Python application may still be starting up.</p>
            <p>If you continue to see this page, check the application logs for errors.</p>
          </div>
          <p>Server time: ${new Date().toISOString()}</p>
        </body>
      </html>
    `);
    return;
  }
  
  // API status endpoint
  if (req.url === '/api/status') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'running',
      service: 'fallback Node.js server',
      timestamp: new Date().toISOString(),
      environment: process.env.NODE_ENV || 'unknown'
    }));
    return;
  }
  
  // For all other requests
  res.writeHead(404, { 'Content-Type': 'text/plain' });
  res.end('Not Found');
});

server.listen(port, () => {
  console.log(`Fallback server running on port ${port}`);
}); 