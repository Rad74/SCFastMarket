import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Con VITE_USE_API=1 le chiamate /api vanno al tuo backend (porta 8000)
export default defineConfig({
  plugins: [vue()],
  server: { proxy: { '/api': 'http://localhost:8000' } },
})
