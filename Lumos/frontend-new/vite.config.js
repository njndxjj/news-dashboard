import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: './',
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: process.env.BACKEND_URL || 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    rollupOptions: {
      input: {
        main: 'index.html',
        admin: 'admin.html',
        behavior: 'behavior.html',
        interestGraph: 'interest-graph.html',
      },
    },
  },
})
