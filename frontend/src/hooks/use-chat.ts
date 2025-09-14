import { useQuery } from "@tanstack/react-query";
import { getConversationWithMessages } from "@/api/conversation";
import { MINS_10, MINS_5 } from "@/constants/time";
import type { Conversation } from "@/types/conversation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { sendMessage as sendMessageApi } from "@/api/chat";
import { toast } from "sonner";
import type { AssistantMessageRequest } from "@/types/message";
import { useOptimistic, useCallback, startTransition } from "react";
import type { Message, UserMessage, AssistantMessage } from "@/types/message";
import type { Optimistic } from "@/types/chat";
import { MESSAGE_ROLES } from "@/constants/message-roles";

export const chatQueryKeys = {
    messages: (conversationId: Conversation["id"]) =>
        ["chat", conversationId, "messages"] as const,
} as const;

export const useChatMessages = (conversationId: Conversation["id"]) => {
    return useQuery({
        queryKey: chatQueryKeys.messages(conversationId),
        queryFn: () => getConversationWithMessages(conversationId),
        staleTime: MINS_5,
        gcTime: MINS_10,
        enabled: !!conversationId,
        select: (data) => data?.messages ?? [],
    });
};

export const useSendMessage = (conversationId: Conversation["id"]) => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (variables: AssistantMessageRequest) =>
            sendMessageApi({ ...variables, conversationId }),
        onSuccess: async () => {
            // Minimum delay for UX
            await new Promise((resolve) => setTimeout(resolve, 1000));

            await queryClient.invalidateQueries({
                queryKey: chatQueryKeys.messages(conversationId),
            });
        },
        onError: (error) => {
            toast.error("Failed to send message. Please try again.");
            console.error("Error sending message:", error);
        },
    });
};

export const useChat = (conversationId: Conversation["id"]) => {
    const {
        data: messages = [],
        isLoading: isLoadingMessages,
        error: messagesError,
    } = useChatMessages(conversationId);

    const sendMessageMutation = useSendMessage(conversationId);

    const [optimisticMessages, addOptimisticMessage] = useOptimistic(
        messages,
        (state: Message[], optimisticMessage: Optimistic<Message>) => {
            const nonOptimisticMessages = state.filter(
                (msg) => !("isOptimistic" in msg),
            );
            return [...nonOptimisticMessages, optimisticMessage];
        },
    );

    const sendMessage = useCallback(
        (message: string) => {
            if (sendMessageMutation.isPending) return;

            // Add optimistic user message
            startTransition(() => {
                addOptimisticMessage({
                    id: crypto.randomUUID(),
                    role: MESSAGE_ROLES.USER,
                    content: message,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                    isOptimistic: true,
                } satisfies Optimistic<UserMessage>);
            });

            // Add optimistic assistant message after a delay
            setTimeout(() => {
                startTransition(() => {
                    addOptimisticMessage({
                        id: crypto.randomUUID(),
                        role: MESSAGE_ROLES.ASSISTANT,
                        content: "",
                        created_at: new Date().toISOString(),
                        updated_at: new Date().toISOString(),
                        isOptimistic: true,
                        sources: [],
                    } satisfies Optimistic<AssistantMessage>);
                });
            }, 100);

            sendMessageMutation.mutate({
                message,
                sessionId: `${conversationId}`,
            });
        },
        [sendMessageMutation, conversationId, addOptimisticMessage],
    );

    return {
        messages: optimisticMessages,
        isLoading: sendMessageMutation.isPending,
        isLoadingMessages,
        error:
            sendMessageMutation.error?.message ??
            messagesError?.message ??
            null,
        sendMessage,
    };
};
