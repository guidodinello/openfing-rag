import { useState, useCallback } from "react";

const STORAGE_KEY = "openchat_api_key";

export const getApiKey = () => {
    return localStorage.getItem(STORAGE_KEY);
};

const persistToLocalStorage = (apiKey: string) => {
    localStorage.setItem(STORAGE_KEY, apiKey);
};

const removeFromLocalStorage = () => {
    localStorage.removeItem(STORAGE_KEY);
};

export const useApiKey = () => {
    const [apiKey, setApiKey] = useState<string | null>(() => getApiKey());

    const updateApiKey = useCallback((newKey: string) => {
        persistToLocalStorage(newKey);
        setApiKey(newKey);
    }, []);

    const deleteApiKey = useCallback(() => {
        removeFromLocalStorage();
        setApiKey(null);
    }, []);

    return {
        apiKey,
        updateApiKey,
        deleteApiKey,
    };
};
