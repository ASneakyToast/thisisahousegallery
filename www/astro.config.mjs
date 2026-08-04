import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";
import mdx from "@astrojs/mdx";

export default defineConfig({
  output: "static",
  site: "https://thisisahousegallery.com",
  integrations: [sitemap(), mdx()],
  vite: {
    resolve: {
      alias: {
        "@": new URL("./src", import.meta.url),
      },
    },
  },
});
