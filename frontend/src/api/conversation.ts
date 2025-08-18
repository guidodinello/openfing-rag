import type { ApiResponse } from "@/types/api";
import { privateApiClient } from "./axios";
import type {
    Conversation,
    ConversationWithMessages,
} from "@/types/conversation";

export const getUserConversations = async () => {
    const response =
        await privateApiClient.get<ApiResponse<Conversation[]>>(
            "/conversations",
        );
    return response.data.data;
};

export const getConversationWithMessages = async (
    conversationId: Conversation["id"],
) => {
    const response = await privateApiClient.get<
        ApiResponse<ConversationWithMessages>
    >(`/conversations/${conversationId}/messages`);

    return response.data.data;
};

export const deleteConversation = async (
    conversationId: Conversation["id"],
) => {
    await privateApiClient.delete(`/conversations/${conversationId}`);
};

export const createConversation = async (title?: string) => {
    const response = await privateApiClient.post<ApiResponse<Conversation>>(
        "/conversations",
        {
            title: title ?? "Nueva conversación",
        },
    );
    return response.data.data;
};

export interface UpdateConversationRequest {
    conversationId: Conversation["id"];
    newTitle: string;
}

export const updateConversation = async ({
    conversationId,
    newTitle,
}: UpdateConversationRequest) => {
    const response = await privateApiClient.patch<ApiResponse<Conversation>>(
        `/conversations/${conversationId}`,
        { new_title: newTitle },
    );
    return response.data.data;
};
