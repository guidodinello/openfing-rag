import { privateApiClient } from "./axios";
import type { ApiResponse } from "../types/api";
import type {
    AssistantMessage,
    AssistantMessageRequest,
} from "@/types/message";

interface SendMessageRequest extends AssistantMessageRequest {
    conversationId: number;
}

export const sendMessage = async (data: SendMessageRequest) => {
    const { conversationId, ...requestBody } = data;

    const response = await privateApiClient.post<ApiResponse<AssistantMessage>>(
        "v1/services/generator/chat",
        requestBody,
        { headers: { "X-Conversation-ID": conversationId.toString() } },
    );
    return response.data.data;
};
