import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/tracking': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/tracking/, ''),
        ws: true,
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false
  }
})
