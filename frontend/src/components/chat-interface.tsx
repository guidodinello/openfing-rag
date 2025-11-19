import { useEffect, useRef } from "react";
import { useNavigate } from "react-router";
import { isAxiosError } from "axios";
import { ChatHeader } from "./chat-header";
import { ChatMessages } from "./chat-messages";
import { ChatInput } from "./chat-input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useChat } from "@/hooks/use-chat";
import { useConversationQuery } from "@/hooks/use-conversation";
import { LoadingMessage } from "./loading-message";
import { ErrorMessage } from "./error-message";
import { useScrollToBottom } from "@/hooks/use-scroll";
import { useInitialMessage } from "@/hooks/use-initial-message";
import type { ConversationIdParam } from "@/hooks/use-conversation-id-param";

export const ChatInterface = ({ conversationId: id }: ConversationIdParam) => {
    const navigate = useNavigate();
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const {
        data: conversation,
        isLoading: isLoadingConversation,
        error: conversationError,
        refetch: refetchConversation,
    } = useConversationQuery(id);

    const { messages, sendMessage, isLoading, error, isLoadingMessages } =
        useChat(id);

    useScrollToBottom(messagesEndRef, [messages.length, isLoading]);

    const handleSendMessage = (content: string) => {
        if (isLoading) return;
        sendMessage(content);
    };

    useInitialMessage({
        onMessage: handleSendMessage,
        enabled:
            !isLoading &&
            !isLoadingConversation &&
            !isLoadingMessages &&
            messages.length === 0 &&
            !!conversation,
    });

    useEffect(() => {
        if (conversationError && !isLoadingConversation) {
            if (isAxiosError(conversationError)) {
                const status = conversationError.response?.status;
                if (status === 404 || status === 401 || status === 403) {
                    void navigate("/", { replace: true });
                }
            }
        }
    }, [conversationError, isLoadingConversation, navigate]);

    if (isLoadingConversation) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[80vh] p-4">
                <LoadingMessage />
                <p className="text-muted-foreground mt-4">
                    Cargando conversación...
                </p>
            </div>
        );
    }

    if (conversationError) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[80vh] p-4">
                <ErrorMessage
                    error={
                        conversationError instanceof Error
                            ? conversationError.message
                            : "Error al cargar la conversación"
                    }
                    onRetry={() => refetchConversation()}
                />
            </div>
        );
    }

    if (!conversation) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[80vh] p-4">
                <p className="text-muted-foreground">
                    Conversación no encontrada
                </p>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-screen">
            <ChatHeader conversationTitle={conversation.title} />

            <div className="flex-1 flex flex-col min-h-0 mx-auto w-full max-w-4xl px-4 md:px-12 pt-4 pb-8">
                <ScrollArea className="flex-1">
                    <ChatMessages
                        messages={messages}
                        isLoading={isLoading}
                        error={error}
                    />
                    <div ref={messagesEndRef} />
                </ScrollArea>

                <div className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                    <div className="p-4">
                        <ChatInput
                            onSendMessage={handleSendMessage}
                            disabled={isLoading}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
};
