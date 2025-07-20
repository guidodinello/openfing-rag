import { getApiKey } from "@/hooks/use-api-key";
import axios, { type AxiosError } from "axios";

export const publicApiClient = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    timeout: 30000,
    headers: {
        "Content-Type": "application/json",
    },
});

export const privateApiClient = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    timeout: 30000,
    headers: {
        "Content-Type": "application/json",
    },
});

privateApiClient.interceptors.request.use(
    (config) => {
        const apiKey = getApiKey();
        if (apiKey) {
            config.headers.set("X-API-Key", apiKey);
        }
        return config;
    },
    (error: AxiosError) => {
        return Promise.reject(error);
    },
);

[privateApiClient, publicApiClient].forEach((client) => {
    client.interceptors.response.use(
        (response) => response,
        (error: AxiosError) => {
            if (error.response?.status === 401) {
                console.warn(
                    "Invalid API key - please check your configuration",
                );
            } else if (error.response?.status === 429) {
                console.warn("Rate limit exceeded - please try again later");
            } else if (error.code === "ECONNABORTED") {
                console.warn("Request timeout - please try again");
            }

            return Promise.reject(error);
        },
    );
});
