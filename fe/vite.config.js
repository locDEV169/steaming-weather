import { defineConfig } from "vite";
import preact from "@preact/preset-vite";
import { apiProxy } from "./middleware/api-proxy.js";

export default defineConfig({
  plugins: [preact()],
  publicDir: "../cron-data/data",
  server: {
    host: "127.0.0.1",
    proxy: apiProxy,
  },
  preview: {
    host: "127.0.0.1",
    proxy: apiProxy,
  },
});
