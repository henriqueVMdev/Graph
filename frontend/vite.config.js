import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  // O plotly.js-dist-min vinha pre-empacotado pelo browserify, que injetava o
  // shim de `global`. Consumindo o pacote-fonte esse shim nao existe mais e
  // has-hover (dependencia do modulo de hover) quebra com "global is not
  // defined" na primeira vez que um grafico monta.
  define: {
    global: 'globalThis',
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    chunkSizeWarningLimit: 1800,
    rollupOptions: {
      output: {
        // Os sete modulos viram um chunk so: sao sempre carregados juntos por
        // composables/plotly.js, entao separa-los seria sete requisicoes para
        // o mesmo momento.
        manualChunks: {
          plotly: [
            'plotly.js/lib/core',
            'plotly.js/lib/scatter',
            'plotly.js/lib/bar',
            'plotly.js/lib/heatmap',
            'plotly.js/lib/histogram',
            'plotly.js/lib/candlestick',
            'plotly.js/lib/scatterpolar',
          ],
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
})
