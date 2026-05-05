import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: '/app/hot/',
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:5050',
    },
  },
})
