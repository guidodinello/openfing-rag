import { useAuthStore } from "@/stores/auth-store";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { login, logout, register } from "@/api/auth";

export const useLogin = () => {
    const { setTokens } = useAuthStore();
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: login,
        onSuccess: (data) => {
            setTokens(data.access_token, data.refresh_token!);
            queryClient.invalidateQueries({ queryKey: ["user"] });
            toast.success("Successfully logged in!");
        },
        onError: (error) => {
            console.error("Login error:", error);
            toast.error("Oops! There was a problem with the login attempt");
        },
    });
};

export const useRegister = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: register,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["user"] });
            toast.success("Successfully registered!");
        },
        onError: (error) => {
            console.error("Register error:", error);
            toast.error("Oops! There was a problem with the register attempt");
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
