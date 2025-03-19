# Setup Instructions for Email Forwarder UI

The error you're seeing is related to missing Vite dependencies in the frontend React application. Here's how to fix it:

## Fix for "Cannot find module 'vite'" Error

1. First, make sure you have Node.js installed (version 16 or newer recommended)

2. Fix the frontend dependencies:

```bash
# Navigate to the frontend directory
cd email_forwarder/frontend

# Remove any existing node_modules and package-lock
rm -rf node_modules package-lock.json

# Install dependencies
npm install

# Try running the development server
npm run dev
```

3. If you're still having issues, try creating a new Vite app from scratch:

```bash
# Navigate to the email_forwarder directory
cd email_forwarder

# Backup existing frontend
mv frontend frontend_old

# Create a new Vite React app
npx create-vite@latest frontend --template react

# Install dependencies
cd frontend
npm install

# Install UI dependencies
npm install @mui/material @mui/icons-material @emotion/react @emotion/styled axios react-router-dom @mui/lab

# Start the development server
npm run dev
```

4. Copy the component files from the original project:

   - From `frontend_old/src/components` to `frontend/src/components`
   - From `frontend_old/src/pages` to `frontend/src/pages`
   - From `frontend_old/src/services` to `frontend/src/services`

5. Update the main app files:
   - `App.jsx`
   - `main.jsx`
   - `vite.config.js` (add proxy configuration)

## Running the Application

### Development Mode

```bash
# In one terminal, start the backend
cd email_forwarder
python main.py

# In another terminal, start the frontend
cd email_forwarder/frontend
npm run dev
```

### Production Mode

```bash
# Build the frontend
cd email_forwarder/frontend
npm run build

# Start the backend which will serve the frontend
cd email_forwarder
python main.py
```

The application will be available at:

- Development: http://localhost:5173 (frontend) and http://localhost:8000 (backend)
- Production: http://localhost:8000 (both frontend and backend)
