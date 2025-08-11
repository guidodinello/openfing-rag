import axios, {
    type AxiosResponse,
    type InternalAxiosRequestConfig,
    AxiosError,
    HttpStatusCode,
} from "axios";
import { useAuthStore } from "@/stores/auth-store";
import { toast } from "sonner";
import { refreshToken } from "./auth";
import { MINS_5 } from "@/constants/time";

const handleCommonErrors = (error: AxiosError) => {
    const status = error.response?.status;

    switch (status) {
        case HttpStatusCode.Forbidden:
            toast.error("Insufficient permissions for this operation");
            break;
        case HttpStatusCode.UnprocessableEntity:
            console.error("Validation error 422:", error.response?.data);
            break;
        case HttpStatusCode.TooManyRequests:
            toast.error("Rate limit exceeded - please try again later");
            break;
        case HttpStatusCode.InternalServerError:
            toast.error("Server error - please try again later");
            break;
        default:
            if (error.code === AxiosError.ECONNABORTED) {
                toast.error("Request timeout - please try again");
            } else if (error.code === AxiosError.ERR_NETWORK) {
                toast.error("Network error - please check your connection");
            }
            break;
    }
};

const baseApiConfiguration = {
    baseURL: import.meta.env.VITE_API_URL,
    timeout: MINS_5,
    headers: { "Content-Type": "application/json" },
};

export const publicApiClient = axios.create(baseApiConfiguration);
export const privateApiClient = axios.create(baseApiConfiguration);

privateApiClient.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        const { getValidatedAccessToken } = useAuthStore.getState();
        const token = getValidatedAccessToken();

        if (token) {
            config.headers.set("Authorization", `Bearer ${token}`);
        }

        const apiKey = localStorage.getItem("api_key");
        if (apiKey) {
            config.headers.set("X-API-Key", apiKey);
        }

        return config;
    },
    (error: AxiosError) => Promise.reject(error),
);

privateApiClient.interceptors.response.use(
    (response: AxiosResponse) => response,
    async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & {
            _retry?: boolean;
        };
        const status = error.response?.status;

        if (
            status === HttpStatusCode.Unauthorized &&
            originalRequest &&
            !originalRequest._retry
        ) {
            originalRequest._retry = true;

            try {
                const {
                    refreshToken: storedRefreshToken,
                    setTokens,
                    clearAuth,
                } = useAuthStore.getState();

                if (!storedRefreshToken) {
                    clearAuth();
                    return Promise.reject(error);
                }

                const { access_token, refresh_token } = await refreshToken({
                    refresh_token: storedRefreshToken,
                });

                setTokens(access_token, refresh_token || storedRefreshToken);
                originalRequest.headers.set(
                    "Authorization",
                    `Bearer ${access_token}`,
                );

                return privateApiClient(originalRequest);
            } catch (refreshError) {
                console.error("Token refresh failed:", refreshError);
                toast.error("Session expired. Please log in again.");
                useAuthStore.getState().clearAuth();
                return Promise.reject(refreshError);
            }
        }

        if (status === HttpStatusCode.Unauthorized) {
            toast.error("Authentication failed. Please log in again.");
            useAuthStore.getState().clearAuth();
        }

        handleCommonErrors(error);
        return Promise.reject(error);
    },
);

publicApiClient.interceptors.response.use(
    (response: AxiosResponse) => response,
    async (error: AxiosError) => {
        const status = error.response?.status;

        if (status === HttpStatusCode.Unauthorized) {
            toast.error(
                "Authentication failed. Please check your credentials.",
            );
        }

        handleCommonErrors(error);
        return Promise.reject(error);
    },
);
