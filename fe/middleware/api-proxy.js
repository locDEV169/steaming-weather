/** Vite-only proxy options for /api → Flask (dev + preview). */
export const apiProxy = {
  "/api": {
    target: "http://127.0.0.1:5000",
    changeOrigin: true,
  },
};
