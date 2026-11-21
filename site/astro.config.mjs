// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// For GitHub Pages set SITE_URL=https://<user>.github.io and SITE_BASE=/<repo> (done in the workflow).
export default defineConfig({
  integrations: [sitemap()],
  site: process.env.SITE_URL ?? 'https://mangagrove.ashishsingh92003.workers.dev',
  base: process.env.SITE_BASE ?? '/',
});
