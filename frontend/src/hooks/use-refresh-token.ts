// hooks/use-refresh-token.ts
import { useEffect, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { useAuthStore } from "@/stores/auth-store";
import { refreshToken } from "@/api/auth";

export const useRefreshToken = () => {
    const { rememberMe, setAccessToken, clearAuth, isAuthenticated } =
        useAuthStore();
    const hasAttempted = useRef(false);

    const { mutate, isPending } = useMutation({
        mutationFn: refreshToken,
        onSuccess: (data) => setAccessToken(data.access_token, rememberMe),
        onError: (error) => {
            console.error("Auto-refresh failed:", error);
            clearAuth();
        },
    });

    useEffect(() => {
        if (hasAttempted.current || !rememberMe || isAuthenticated) return;
        hasAttempted.current = true;

        mutate();
    }, [rememberMe, isAuthenticated, mutate]);

    return { isPending };
};
