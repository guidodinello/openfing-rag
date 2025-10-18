/// <reference types="vite/client" />

interface ImportMetaEnv {
    readonly VITE_API_URL: string;
    readonly VITE_APP_VERSION: string;

    readonly VITE_SENTRY_DSN: string | undefined;
    readonly VITE_SENTRY_ORG: string | undefined;
    readonly VITE_SENTRY_PROJECT: string | undefined;
}

interface ImportMeta {
    readonly env: ImportMetaEnv;
}
