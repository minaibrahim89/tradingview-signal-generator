import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    server: {
        proxy: {
            '/api/v1': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                secure: false,
                // No rewrite needed as the backend expects /api/v1
            },
            '/health': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                secure: false
            }
        },
    },
    build: {
        outDir: '../static',
        emptyOutDir: true,
    },
}); 