import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

interface ApiKeyState {
    apiKey: string | null;
}

interface ApiKeyActions {
    setApiKey: (apiKey: string) => void;
    clearApiKey: () => void;
}

export const useApiKeyStore = create<ApiKeyState & ApiKeyActions>()(
    persist(
        (set) => ({
            apiKey: null,
            setApiKey: (apiKey) => set({ apiKey }),
            clearApiKey: () => set({ apiKey: null }),
        }),
        {
            name: "openchat_api_key",
            storage: createJSONStorage(() => localStorage),
        },
    ),
);
