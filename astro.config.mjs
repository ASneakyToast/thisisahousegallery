import { defineConfig } from 'astro/config';
import vue from "@astrojs/vue";
import { astroImageTools } from "astro-imagetools";
import svelte from "@astrojs/svelte";

// https://astro.build/config
export default defineConfig({
  site: "https://thisisahousegallery.com/",
  integrations: [vue(), svelte(), astroImageTools]
});
