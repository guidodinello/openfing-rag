import { useAuthStore } from "@/stores/auth-store";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { login, logout, register } from "@/api/auth";
import type { RegisterCredentials } from "@/types/auth";
import { isValidationError } from "@/utils/errors";
import { type ValidationErrorResponse } from "@/types/api";

export const useLogin = () => {
    const setTokens = useAuthStore((state) => state.setTokens);
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: login,
        onSuccess: (data) => {
            setTokens(data.access_token, data.refresh_token!);
            void queryClient.invalidateQueries({ queryKey: ["user"] });
            toast.success(`Welcome back!`);
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
    const setTokens = useAuthStore((state) => state.setTokens);
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (
            registerData: Omit<RegisterCredentials, "confirmPassword">,
        ) => {
            const user = await register(registerData);

            const loginData = await login({
                username: registerData.username,
                password: registerData.password,
            });

            return { user, tokens: loginData };
        },
        onSuccess: ({ user, tokens }) => {
            setTokens(tokens.access_token, tokens.refresh_token!);
            void queryClient.invalidateQueries({ queryKey: ["user"] });
            toast.success(`Welcome ${user.username}!`);
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

    return useMutation({
        mutationFn: logout,
        onSuccess: () => {
            queryClient.clear();
            toast.success("Successfully logged out!");
        },
        onError: (error) => {
            queryClient.clear();
            console.error("Logout error:", error);
            toast.success("Successfully logged out!");
        },
    });
};
