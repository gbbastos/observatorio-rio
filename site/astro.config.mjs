// @ts-check
import { defineConfig } from 'astro/config';

// SITE_URL e SITE_BASE vêm do deploy (GitHub Pages publica em /<repositório>/); localmente, raiz.
export default defineConfig({
  site: process.env.SITE_URL || 'http://localhost:4321',
  base: process.env.SITE_BASE || '/',
  trailingSlash: 'ignore',
  build: { format: 'directory' },
});
