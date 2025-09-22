import { privateApiClient, publicApiClient } from "./axios";
import type { ApiResponse } from "../types/api";
import type {
    AssistantMessage,
    AssistantMessageRequest,
} from "@/types/message";
import type { ChatResponse } from "@/types/chat";
import { MESSAGE_ROLES } from "@/constants/message-roles";

const transformChatResponseToAssistantMessage = (
    chatAnswer: ChatResponse,
): AssistantMessage => {
    return {
        id: chatAnswer.id.toString(),
        content: chatAnswer.answer.answer,
        role: MESSAGE_ROLES.ASSISTANT,
        sources: chatAnswer.sources,
        created_at: chatAnswer.timestamp,
        updated_at: chatAnswer.timestamp,
    };
};

interface SendMessageRequest extends AssistantMessageRequest {
    conversationId: number;
}

export const sendMessage = async (data: SendMessageRequest) => {
    const { conversationId, ...requestBody } = data;

    const response = await privateApiClient.post<ApiResponse<ChatResponse>>(
        "/services/generator/chat",
        requestBody,
        {
            headers: {
                "X-Conversation-ID": conversationId.toString(),
            },
        },
    );

    return {
        ...response,
        data: transformChatResponseToAssistantMessage(response.data.data),
    };
};

interface SendAnonymousMessageRequest extends AssistantMessageRequest {
    sessionId: string;
}

export const sendAnonymousMessage = async (
    data: SendAnonymousMessageRequest,
) => {
    const { sessionId, ...requestBody } = data;

    const response = await publicApiClient.post<ApiResponse<ChatResponse>>(
        "/services/generator/chat",
        requestBody,
        {
            headers: {
                "X-Session-ID": sessionId,
            },
        },
    );

    return {
        ...response,
        data: transformChatResponseToAssistantMessage(response.data.data),
        // Preserve headers for session ID updates
        headers: response.headers,
    };
};
