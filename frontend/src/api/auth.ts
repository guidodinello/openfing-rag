import { useAuthStore } from "@/stores/auth-store";
import { publicApiClient, privateApiClient } from "./axios";
import type {
    LoginCredentials,
    RegisterCredentials,
    RegisterResponse,
    TokenResponse,
} from "@/types/auth";
import type { ApiResponse } from "@/types/api";

export const login = async ({ username, password }: LoginCredentials) => {
    const formData = new FormData();
    formData.append("grant_type", "password");
    formData.append("username", username);
    formData.append("password", password);

    const response = await publicApiClient.post<TokenResponse>(
        "/auth/login",
        formData,
        {
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
        },
    );

    return response.data;
};

export const register = async (
    data: Omit<RegisterCredentials, "confirmPassword">,
) => {
    const response = await publicApiClient.post<ApiResponse<RegisterResponse>>(
        "/auth/register",
        data,
    );

    return response.data.data;
};

export const refreshToken = async () => {
    const response = await publicApiClient.post<TokenResponse>(
        "/auth/refresh",
        {},
    );

    return response.data;
};

export const logout = async () => {
    try {
        await privateApiClient.post("/auth/logout", {});
    } catch (error) {
        console.error("Logout error:", error);
    } finally {
        useAuthStore.getState().clearAuth();
    }
};
