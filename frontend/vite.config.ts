import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://192.168.1.200',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://192.168.1.200',
        ws: true,
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: '../app/static',
    assetsDir: 'assets',
    minify: 'terser',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks: undefined
      }
    }
  }
})
