// @ts-check
import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
  site: 'https://thisisahousegallery.com',
  output: 'static',
  // The CMS API base URL is env-overridable so the same codebase can build
  // against localhost (default) or a remote/public CMS URL.
});