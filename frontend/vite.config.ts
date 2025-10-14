import { sentryVitePlugin } from "@sentry/vite-plugin";
import { defineConfig, type PluginOption } from "vite";
import path from "path";
import react from "@vitejs/plugin-react-swc";
import tailwindcss from "@tailwindcss/vite";
import { visualizer } from "rollup-plugin-visualizer";

// https://vite.dev/config/
export default defineConfig({
    plugins: [
        react(),
        tailwindcss(),
        visualizer({
            open: false,
            gzipSize: true,
            brotliSize: true,
            filename: "dist/stats.html",
        }) as PluginOption,
        sentryVitePlugin({
            org: process.env.VITE_SENTRY_ORG,
            project: process.env.VITE_SENTRY_PROJECT,
            disable: process.env.NODE_ENV !== "production",
        }),
    ],

    envDir: path.resolve(__dirname, "../"),

    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./src"),
        },
    },

    server: {
        proxy: {
            "/api": {
                target: "http://localhost:8000",
                changeOrigin: true,
            },
        },
    },

    optimizeDeps: {
        exclude: [],
        include: [
            "react",
            "react-dom",
            "react-router",
            "zustand",
            "@tanstack/react-query",
            "axios",
        ],
    },

    build: {
        sourcemap: process.env.NODE_ENV === "development",

        rollupOptions: {
            output: {
                chunkFileNames: "assets/[name]-[hash].js",
                entryFileNames: "assets/[name]-[hash].js",
                assetFileNames: "assets/[name]-[hash].[ext]",
                manualChunks: (id) => {
                    if (id.includes("node_modules")) {
                        if (id.includes("react") || id.includes("scheduler")) {
                            return "react-core";
                        }

                        if (
                            id.includes("zustand") ||
                            id.includes("@tanstack/react-query")
                        ) {
                            return "react-state";
                        }

                        if (id.includes("@radix-ui")) {
                            return "ui-radix";
                        }

                        if (
                            id.includes("react-hook-form") ||
                            id.includes("zod") ||
                            id.includes("@hookform")
                        ) {
                            return "forms";
                        }

                        if (
                            id.includes("react-markdown") ||
                            id.includes("remark")
                        ) {
                            return "markdown";
                        }

                        if (id.includes("shiki") && !id.includes("/langs/")) {
                            return "shiki-core";
                        }

                        if (id.includes("react-icons")) {
                            return "icons";
                        }

                        if (id.includes("@sentry")) {
                            return "sentry";
                        }
                    }
                },
            },
        },
    },
});
