import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // Required for Docker
    port: 5173,
    strictPort: true // Force it to crash instead of switching to 5174
  }
})
