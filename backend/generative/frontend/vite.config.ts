import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";

export default defineConfig({
    plugins: [svelte()],
    server: {
        host: true, // Needed to access from outside container
        port: 5173, // Default Vite port, matching Nginx config
        watch: {
            usePolling: true, // Needed for hot reload in Docker
        },
    },
    // Add these for better Docker compatibility
    optimizeDeps: {
        exclude: ["@sveltejs/kit"], // Avoid potential build issues
    },
    // Optional: configure environment variables
    define: {
        "process.env.NODE_ENV": JSON.stringify(process.env.NODE_ENV),
    },
});
