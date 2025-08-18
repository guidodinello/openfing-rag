import { useOptimistic, useCallback, startTransition, useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { sendMessage as sendMessageApi } from "@/api/chat";
import type { AxiosError } from "axios";
import { toast } from "sonner";
import { MINS_10, MINS_5 } from "@/constants/time";
import type { Conversation } from "@/types/conversation";
import { getConversationWithMessages } from "@/api/conversation";
import type {
    AssistantMessage,
    AssistantMessageRequest,
    Message,
    UserMessage,
} from "@/types/message";
import type { Optimistic } from "@/types/chat";

export const chatQueryKeys = {
    messages: (conversationId: Conversation["id"]) =>
        ["chat", conversationId, "messages"] as const,
} as const;

export const useChatMutation = (conversationId: Conversation["id"]) => {
    const queryClient = useQueryClient();

    const {
        data: conversation,
        isLoading: isLoadingMessages,
        error: messagesError,
    } = useQuery({
        queryKey: chatQueryKeys.messages(conversationId),
        queryFn: () => getConversationWithMessages(conversationId),
        staleTime: MINS_5,
        gcTime: MINS_10,
        enabled: !!conversationId,
    });

    const messages = useMemo(
        () => conversation?.messages ?? [],
        [conversation?.messages],
    );

    const [optimisticMessages, addOptimisticMessage] = useOptimistic(
        messages,
        (state: Message[], optimisticMessage: Optimistic<Message>) => {
            const nonOptimisticMessages = state.filter(
                (msg) => !("isOptimistic" in msg),
            );
            return [...nonOptimisticMessages, optimisticMessage];
        },
    );

    const sendMessageMutation = useMutation({
        mutationFn: (variables: AssistantMessageRequest) =>
            sendMessageApi({ ...variables, conversationId }),
        onMutate: async (variables: AssistantMessageRequest) => {
            await queryClient.cancelQueries({
                queryKey: chatQueryKeys.messages(conversationId),
            });

            const userMessageId = crypto.randomUUID();
            const assistantMessageId = crypto.randomUUID();

            startTransition(() => {
                addOptimisticMessage({
                    id: userMessageId,
                    role: "user",
                    content: variables.message,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                    isOptimistic: true,
                } satisfies Optimistic<UserMessage>);
            });

            setTimeout(() => {
                startTransition(() => {
                    addOptimisticMessage({
                        id: assistantMessageId,
                        role: "assistant",
                        content: "",
                        created_at: new Date().toISOString(),
                        updated_at: new Date().toISOString(),
                        isOptimistic: true,
                        sources: [],
                    } satisfies Optimistic<AssistantMessage>);
                });
            }, 100);

            return { userMessageId, assistantMessageId };
        },
        onSuccess: async () => {
            // Minimum delay for UX
            await new Promise((resolve) => setTimeout(resolve, 1000));

            await queryClient.invalidateQueries({
                queryKey: chatQueryKeys.messages(conversationId),
            });
        },
        onError: (error: AxiosError, _, context) => {
            if (context) {
                startTransition(() => {
                    queryClient.invalidateQueries({
                        queryKey: chatQueryKeys.messages(conversationId),
                    });
                });
            }

            if (error.response?.status === 401) {
                toast.error("Please setup an API Key in the settings.");
            } else {
                toast.error("Failed to send message. Please try again.");
            }
        },
    });

    const sendMessage = useCallback(
        (message: string) => {
            if (sendMessageMutation.isPending) {
                return;
            }

            sendMessageMutation.mutate({
                message: message,
                sessionId: `${conversationId}`,
            });
        },
        [sendMessageMutation, conversationId],
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
