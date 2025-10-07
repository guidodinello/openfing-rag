import { useAuthStore } from "@/stores/auth-store";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { login, logout, register } from "@/api/auth";
import type { RegisterCredentials, LoginCredentials } from "@/types/auth";
import { isValidationError } from "@/utils/errors";
import { type ValidationErrorResponse } from "@/types/api";
import { useNavigate } from "react-router";

interface LoginParams {
    credentials: LoginCredentials;
    rememberMe?: boolean;
}

export const useLogin = () => {
    const setAccessToken = useAuthStore((state) => state.setAccessToken);
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ credentials }: LoginParams) => login(credentials),
        onSuccess: (data, variables) => {
            setAccessToken(data.access_token, variables.rememberMe);
            void queryClient.invalidateQueries({ queryKey: ["user"] });
            toast.success("Welcome back!");
        },
        onError: (error) => {
            console.error("Login error:", error);

            if (!isValidationError(error)) {
                toast.error("Oops! There was a problem with the login attempt");
                return;
            }

            const response = error.response?.data as ValidationErrorResponse;
            toast.error(
                response.message ?? response.detail ?? "Unexpected error",
            );
        },
    });
};

export const useRegister = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (
            registerData: Omit<RegisterCredentials, "confirmPassword">,
        ) => {
            return await register(registerData);
        },
        onSuccess: (data) => {
            void queryClient.invalidateQueries({ queryKey: ["user"] });
            toast.success(`Welcome ${data.username}!`);
        },
        onError: (error) => {
            console.error("Register error:", error);

            if (!isValidationError(error)) {
                toast.error("Oops! There was a problem creating your account");
                return;
            }

            const response = error.response?.data as ValidationErrorResponse;
            toast.error(
                response.message ?? response.detail ?? "Unexpected error",
            );
        },
    });
};

export const useLogout = () => {
    const queryClient = useQueryClient();
    const navigate = useNavigate();
    return useMutation({
        mutationFn: logout,
        onError: (error) => console.error("Logout error:", error),
        onSettled: () => {
            queryClient.clear();
            void navigate("/");
            toast.success("Successfully logged out!");
        },
    });
};
