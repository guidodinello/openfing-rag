import { getUserProfileData } from "@/api/user";
import { MINS_5 } from "@/constants/time";
import { useAuthStore } from "@/stores/auth-store";
import { useQuery } from "@tanstack/react-query";

export const useUserProfileQuery = () => {
    const { isAuthenticated } = useAuthStore();
    return useQuery({
        queryKey: ["users", "me"],
        queryFn: getUserProfileData,
        enabled: isAuthenticated,
        staleTime: MINS_5,
    });
};
