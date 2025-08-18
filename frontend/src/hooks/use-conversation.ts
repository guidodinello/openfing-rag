import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
    createConversation,
    deleteConversation,
    getConversationWithMessages,
    getUserConversations,
    updateConversation,
    type UpdateConversationRequest,
} from "@/api/conversation";
import type { Conversation } from "@/types/conversation";
import { toast } from "sonner";
import { useNavigate } from "react-router";
import { useCallback } from "react";

export const useConversationsQuery = () =>
    useQuery({
        queryKey: ["conversations"],
        queryFn: getUserConversations,
    });

export const useConversationQuery = (conversationId: Conversation["id"]) =>
    useQuery({
        queryKey: ["conversations", conversationId],
        queryFn: () => getConversationWithMessages(conversationId),
        enabled: conversationId !== null,
    });

export const useDeleteConversationMutation = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: deleteConversation,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["conversations"] });
        },
    });
};

export const useUpdateConversationMutation = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: UpdateConversationRequest) =>
            updateConversation(data),

        onSuccess: (updatedConversation) => {
            queryClient.invalidateQueries({ queryKey: ["conversations"] });
            queryClient.setQueryData(
                ["conversations", updatedConversation.id],
                updatedConversation,
            );
            toast.success("Conversación renombrada exitosamente");
        },

        onError: (error) => {
            console.error(`useUpdateConversationMutation ${error}`);
            toast.error("Error al renombrar la conversación");
        },
    });
};

const generateTitle = (firstMessage?: string) => {
    if (!firstMessage) return "Nueva Conversación";
    return firstMessage.length > 50
        ? firstMessage.substring(0, 47) + "..."
        : firstMessage;
};

const useCreateConversationMutation = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: createConversation,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["conversations"] });
        },
    });
};

export const useConversationCreation = () => {
    const navigate = useNavigate();
    const { mutateAsync: createConversation, isPending } =
        useCreateConversationMutation();

    const createNewConversation = useCallback(
        async (initialMessage?: string) => {
            try {
                const conversation = await createConversation(
                    generateTitle(initialMessage),
                );

                const navigationState = initialMessage
                    ? { state: { initialMessage } }
                    : {};

                navigate(`/conversation/${conversation.id}`, {
                    ...navigationState,
                    replace: true,
                });

                return conversation;
            } catch (error) {
                console.error("Failed to create conversation:", error);
                toast.error("Error al crear la conversación");
                throw error;
            }
        },
        [createConversation, navigate],
    );

    return {
        createNewConversation,
        isCreating: isPending,
    };
};
