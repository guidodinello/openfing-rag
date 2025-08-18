import { privateApiClient } from "./axios";
import type { ApiResponse } from "@/types/api";
import type { User } from "@/types/user";

export const getUserProfileData = async () => {
    const response = await privateApiClient.get<ApiResponse<User>>("/users/me");
    return response.data.data;
};
