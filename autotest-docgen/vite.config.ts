import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: 'localhost',
    proxy: {
      // توجيه طلبات المصادقة إلى Gateway
      '/api/token': {
        target: 'http://localhost:80', // Nginx Gateway
        changeOrigin: true,
        secure: false,
        configure: (proxy) => {
          proxy.on('error', (err) => {
            console.log('Token Proxy error:', err);
          });
          proxy.on('proxyReq', (_proxyReq, req, _res) => {
            console.log('Sending Token Request:', req.method, req.url);
          });
        }
      },
      // توجيه طلبات UPM إلى Gateway
      '/api/upm': {
        target: 'http://localhost:80', // Nginx Gateway
        changeOrigin: true,
        secure: false,
        configure: (proxy) => {
          proxy.on('error', (err) => {
            console.log('UPM Proxy error:', err);
          });
          proxy.on('proxyReq', (_proxyReq, req, _res) => {
            console.log('Sending UPM Request:', req.method, req.url);
          });
        }
      },
      // توجيه طلبات AI إلى Gateway
      '/api/analysis': {
        target: 'http://localhost:80', // Nginx Gateway
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api\/analysis/, '/api/analysis'),  // ضمن عدم إزالة subpath
        configure: (proxy) => {
          proxy.on('error', (err) => {
            console.error('❌ AI Proxy error:', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('📤 Sending AI Request:', {
              method: req.method,
              url: req.url,
              headers: proxyReq.getHeaders(),
              contentType: req.headers['content-type']
            });
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('📥 Received AI Response:', {
              statusCode: proxyRes.statusCode,
              statusMessage: proxyRes.statusMessage,
              headers: proxyRes.headers,
              url: req.url
            });
          });
        }
      },
      // توجيه طلبات Notifications إلى Gateway
      '/api/notifications': {
        target: 'http://localhost:80', // Nginx Gateway
        changeOrigin: true,
        secure: false,
        configure: (proxy) => {
          proxy.on('error', (err) => {
            console.log('Notifications Proxy error:', err);
          });
          proxy.on('proxyReq', (_proxyReq, req, _res) => {
            console.log('Sending Notifications Request:', req.method, req.url);
          });
        }
      },
    },
  },
})