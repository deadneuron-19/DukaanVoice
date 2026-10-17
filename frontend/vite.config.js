import { defineConfig } from "vitest/config";
import { loadEnv } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig(function (_a) {
    var mode = _a.mode;
    var env = loadEnv(mode, ".", "VITE_");
    return {
        plugins: [react()],
        server: {
            proxy: {
                "/api": {
                    target: env.VITE_API_PROXY_TARGET || "http://127.0.0.1:8000",
                    changeOrigin: true,
                    rewrite: function (path) { return path.replace(/^\/api/, ""); },
                },
            },
        },
        test: {
            environment: "jsdom",
            setupFiles: ["./tests/setup.ts"],
            css: true,
        },
    };
});
