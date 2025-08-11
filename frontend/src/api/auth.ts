import { useAuthStore } from "@/stores/auth-store";
import { publicApiClient } from "./axios";
import type {
    JwtToken,
    BearerTokenResponse,
    RegisterResponse,
    LoginCredentials,
} from "@/types/auth";
import type { ApiResponse } from "@/types/api";

export const login = async ({ username, password }: LoginCredentials) => {
    const formData = new FormData();
    formData.append("grant_type", "password");
    formData.append("username", username);
    formData.append("password", password);

    const response = await publicApiClient.post<BearerTokenResponse>(
        "/login",
        formData,
        {
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
        },
    );

    return response.data;
};

interface RegisterCredentials {
    email: string;
    username: string;
    password: string;
}

export const register = async (data: RegisterCredentials) => {
    const response = await publicApiClient.post<ApiResponse<RegisterResponse>>(
        "/register",
        data,
    );

    return response.data.data;
};

interface RefreshTokenRequest {
    refresh_token: JwtToken;
}

export const refreshToken = async (data: RefreshTokenRequest) => {
    const response = await publicApiClient.post<BearerTokenResponse>(
        "/refresh",
        data,
    );

    return response.data;
};

export const logout = async () => useAuthStore.getState().clearAuth();
