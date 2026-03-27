import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import path from 'path';

// Import local app configurations
import portfolioInputs from './portfolio_snapshot/vite.config.js';

export default defineConfig({
  plugins: [svelte()],
  resolve: {
    alias: {
      '@components': path.resolve(__dirname, 'assets/components')
    }
  },
  build: {
    outDir: path.resolve(__dirname, 'static'),
    emptyOutDir: false,
    rollupOptions: {
      input: {
        'css/app': path.resolve(__dirname, 'assets/scss/app.scss'),
        
        // Merge app-specific entry points
        ...portfolioInputs(__dirname)
      },
      output: {
        entryFileNames: `[name].js`,
        chunkFileNames: `[name].js`,
        assetFileNames: `[name].[ext]`
      }
    }
  }
});
