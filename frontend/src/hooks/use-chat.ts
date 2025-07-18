import { useOptimistic, useCallback, startTransition } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
    AssistantMessageRequest,
    AssistantMessage,
    Message,
    Optimistic,
    UserMessage,
} from "@/types/chat";
import { getMessages, sendMessage as sendMessageApi } from "@/api/chat";
import type { AxiosError } from "axios";
import { toast } from "sonner";

const FIVE_MINUTES = 5 * 60 * 1000;
const TEN_MINUTES = 10 * 60 * 1000;

export const chatQueryKeys = {
    messages: (sessionId: string) => ["chat", "messages", sessionId] as const,
} as const;

export function useChatMutation(sessionId: string) {
    const queryClient = useQueryClient();

    const {
        data: messages = [],
        isLoading: isLoadingMessages,
        error: messagesError,
    } = useQuery({
        queryKey: chatQueryKeys.messages(sessionId),
        queryFn: () => getMessages(sessionId),
        staleTime: FIVE_MINUTES,
        gcTime: TEN_MINUTES,
    });

    const [optimisticMessages, addOptimisticMessage] = useOptimistic(
        messages,
        (state: Message[], optimisticMessage: Optimistic<Message>) => [
            ...state.filter((msg) => !("isOptimistic" in msg)),
            optimisticMessage,
        ],
    );

    const sendMessageMutation = useMutation({
        mutationFn: sendMessageApi,
        onMutate: async (variables: AssistantMessageRequest) => {
            await queryClient.cancelQueries({
                queryKey: chatQueryKeys.messages(sessionId),
            });

            const userMessageId = crypto.randomUUID();
            const assistantMessageId = crypto.randomUUID();

            startTransition(() => {
                const optimisticUserMessage = {
                    id: userMessageId,
                    role: "user",
                    content: variables.message,
                    timestamp: new Date(),
                    isOptimistic: true,
                } satisfies Optimistic<UserMessage>;
                addOptimisticMessage(optimisticUserMessage);
            });

            setTimeout(() => {
                startTransition(() => {
                    const optimisticAssistantMessage = {
                        id: assistantMessageId,
                        role: "assistant",
                        content: "",
                        timestamp: new Date(),
                        isOptimistic: true,
                    } satisfies Optimistic<AssistantMessage>;
                    addOptimisticMessage(optimisticAssistantMessage);
                });
            }, 100);

            return { userMessageId, assistantMessageId };
        },
        onSuccess: async (data: AssistantMessage, variables, context) => {
            // min delay
            await new Promise((resolve) => setTimeout(resolve, 2000));

            queryClient.setQueryData(
                chatQueryKeys.messages(sessionId),
                (oldMessages: Message[] = []) => {
                    return [
                        ...oldMessages,
                        {
                            id: context.userMessageId,
                            role: "user",
                            content: variables.message,
                            timestamp: new Date(),
                        } satisfies UserMessage,
                        {
                            id: data.id,
                            role: "assistant",
                            content: data.content,
                            timestamp: new Date(),
                            sources: data.sources,
                        } satisfies AssistantMessage,
                    ];
                },
            );
        },
        onError: (error: AxiosError, _, context) => {
            queryClient.setQueryData(
                chatQueryKeys.messages(sessionId),
                (oldMessages: Message[] = []) =>
                    oldMessages.filter(
                        (msg) =>
                            !("isOptimistic" in msg) ||
                            (msg.id !== context?.userMessageId &&
                                msg.id !== context?.assistantMessageId),
                    ),
            );

            if (error.response?.status === 401) {
                toast.error("Please setup an API Key in the settings.");
            } else {
                toast.error("Failed to send message. Please try again.");
            }
        },
    });

    const sendMessage = useCallback(
        (message: string) =>
            sendMessageMutation.mutate({
                message: message,
                sessionId: sessionId,
            }),
        [sendMessageMutation, sessionId],
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
}
