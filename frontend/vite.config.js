import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 3000,
    host: '0.0.0.0',  // 允许局域网访问
    proxy: {
      '/api': {
        target: 'http://localhost:5000',  // 服务器内部转发，不经过防火墙
        changeOrigin: true,
        configure: (proxy, options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            console.log('[Vite Proxy] 转发请求:', req.url, '→ http://localhost:5000');
            proxyReq.setHeader('Cache-Control', 'no-cache');
          });
        }
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets'
  }
}) 