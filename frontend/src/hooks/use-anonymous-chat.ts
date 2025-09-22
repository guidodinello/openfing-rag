import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import type { AxiosError } from "axios";
import { sendAnonymousMessage } from "@/api/chat";
import type { Message, UserMessage, AssistantMessage } from "@/types/message";
import { MESSAGE_ROLES } from "@/constants/message-roles";
import { useSessionStore } from "@/stores/session-store";

interface SendAnonymousMessageVariables {
    message: string;
    lessons_ids?: number[];
    courses_ids?: number[];
}

export const useAnonymousChat = () => {
    const sessionId = useSessionStore((state) => state.sessionId);
    const setSessionId = useSessionStore((state) => state.setSessionId);
    const [messages, setMessages] = useState<Message[]>([]);

    const mutation = useMutation({
        mutationFn: async (variables: SendAnonymousMessageVariables) => {
            const response = await sendAnonymousMessage({
                message: variables.message,
                sessionId,
            });

            // Server can update the session ID
            const serverSessionId = response.headers?.["x-session-id"];
            if (serverSessionId && serverSessionId !== sessionId) {
                setSessionId(serverSessionId);
            }

            return response.data;
        },
        onMutate: (variables) => {
            const userMessage: UserMessage = {
                id: `temp-${Date.now()}`,
                content: variables.message,
                role: MESSAGE_ROLES.USER,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
            };

            setMessages((prev) => [...prev, userMessage]);

            return { userMessage };
        },
        onSuccess: (assistantMessage: AssistantMessage) => {
            setMessages((prev) => [...prev, assistantMessage]);
        },
        onError: (error: AxiosError, _variables, context) => {
            if (context) {
                setMessages((prev) =>
                    prev.filter((msg) => msg.id !== context.userMessage.id),
                );
            }

            console.error("Error sending message:", error);
        },
    });

    return {
        data: messages,
        error: mutation.error?.message,
        isPending:
            messages.length > 0 &&
            messages[messages.length - 1].role === MESSAGE_ROLES.USER,
        isSuccess: mutation.isSuccess,
        sessionId,
        mutate: mutation.mutate,
        reset: mutation.reset,
    };
};
