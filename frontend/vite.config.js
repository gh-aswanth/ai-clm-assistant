import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import react from '@vitejs/plugin-react'
import path from 'path'
import { copyFileSync, mkdirSync, existsSync } from 'fs'

// Copy pdf.worker.min.js to public folder if it doesn't exist
const workerSrc = path.resolve('node_modules/pdfjs-dist/build/pdf.worker.min.mjs')
const publicDir = path.resolve('public')
const destPath = path.resolve(publicDir, 'pdf.worker.min.mjs')

if (existsSync(workerSrc)) {
  if (!existsSync(publicDir)) {
    mkdirSync(publicDir, { recursive: true })
  }
  copyFileSync(workerSrc, destPath)
}

// Knowledge graph: keep in sync with repo root clm/graph_data.json
const graphDataSrc = path.resolve(__dirname, '../graph_data.json')
const graphDataDest = path.resolve(publicDir, 'graph_data.json')
if (existsSync(graphDataSrc)) {
  if (!existsSync(publicDir)) {
    mkdirSync(publicDir, { recursive: true })
  }
  copyFileSync(graphDataSrc, graphDataDest)
}

export default defineConfig({
  plugins: [vue(), react({ include: /\.(jsx|tsx)$/ })],
  server: {
    proxy: {
      '/api': {
        target: 'https://7416-103-158-219-143.ngrok-free.app',
        changeOrigin: true,
      },
      '/ws': {
        target: 'https://7416-103-158-219-143.ngrok-free.app',
        changeOrigin: true,
        ws: true,
      },
    }
  },
  build: {
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks(id) {
          const norm = id.split(path.sep).join('/')
          if (!norm.includes('node_modules/')) return
          if (norm.includes('/pdfjs-dist/')) return 'pdfjs'
          if (norm.includes('/mammoth/')) return 'mammoth'
          if (norm.includes('/react-force-graph-2d/')) return 'react-force-graph'
          if (norm.includes('/react-dom/')) return 'react-dom'
          if (norm.includes('/node_modules/react/')) return 'react'
          if (norm.includes('/vue-router/')) return 'vue-vendor'
          if (norm.includes('/@vue/')) return 'vue-vendor'
          if (norm.includes('/node_modules/vue/')) return 'vue-vendor'
          if (norm.includes('/@tiptap/') || norm.includes('/prosemirror-')) return 'tiptap'
          if (norm.includes('/marked/') || norm.includes('/dompurify/')) return 'markdown'
          if (norm.includes('/axios/')) return 'axios'
          if (norm.includes('/sweetalert2/')) return 'sweetalert2'
          if (norm.includes('/lucide-vue-next/')) return 'lucide'
          return 'vendor'
        },
      },
    },
  },
})
