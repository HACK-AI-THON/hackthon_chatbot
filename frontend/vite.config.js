import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: '0.0.0.0', // Bind to all network interfaces
    strictPort: true,
    hmr: {
      port: 3001
    },
    cors: true,
    // Allow access from any origin for development
    headers: {
      'Access-Control-Allow-Origin': '*',
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})

