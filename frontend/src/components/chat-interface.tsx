import { useRef, useEffect, useState, useCallback } from "react";
import { useLocation, useNavigate } from "react-router";
import { ChatHeader } from "./chat-header";
import { ChatMessages } from "./chat-messages";
import { ChatInput } from "./chat-input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useChat } from "@/hooks/use-chat";
import { useConversationQuery } from "@/hooks/use-conversation";
import { LoadingMessage } from "./loading-message";
import { useConversationIdParam } from "@/hooks/use-conversation-id-param";
import { useScrollToBottom } from "@/hooks/use-scroll";

interface LocationState {
    initialMessage?: string;
}

const useInitialMessage = () => {
    const location = useLocation();
    const [processed, setProcessed] = useState(false);

    const initialMessage = (location.state as LocationState)?.initialMessage;

    const markAsProcessed = useCallback(() => {
        setProcessed(true);
        // Clean up the state
        if (location.state?.initialMessage) {
            const newState = { ...location.state };
            delete newState.initialMessage;
            window.history.replaceState(newState, "");
        }
    }, [location.state]);

    const reset = useCallback(() => {
        setProcessed(false);
    }, []);

    return {
        initialMessage,
        isProcessed: processed,
        markAsProcessed,
        reset,
    };
};

export const ChatInterface = () => {
    const { id } = useConversationIdParam();
    const navigate = useNavigate();
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const {
        initialMessage,
        isProcessed: isInitialMessageProcessed,
        markAsProcessed: markInitialMessageAsProcessed,
        reset: resetInitialMessage,
    } = useInitialMessage();

    const {
        data: conversation,
        isLoading: isLoadingConversation,
        error: conversationError,
    } = useConversationQuery(id);

    const { messages, sendMessage, isLoading, error, isLoadingMessages } =
        useChat(id);

    useScrollToBottom(messagesEndRef, [messages.length, isLoading]);

    const handleSendMessage = useCallback(
        (content: string) => {
            if (isLoading) return;
            sendMessage(content);
        },
        [sendMessage, isLoading],
    );

    // Handle initial message from navigation state
    useEffect(() => {
        const shouldProcessInitialMessage =
            initialMessage &&
            !isInitialMessageProcessed &&
            conversation &&
            messages.length === 0 &&
            !isLoading &&
            !isLoadingConversation &&
            !isLoadingMessages;

        if (shouldProcessInitialMessage) {
            markInitialMessageAsProcessed();
            handleSendMessage(initialMessage);
        }
    }, [
        initialMessage,
        isInitialMessageProcessed,
        conversation,
        messages.length,
        isLoading,
        isLoadingConversation,
        isLoadingMessages,
        handleSendMessage,
        markInitialMessageAsProcessed,
    ]);

    // Reset initial message state when conversation changes
    useEffect(() => {
        resetInitialMessage();
    }, [id, resetInitialMessage]);

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

    if (conversationError || !conversation) {
        navigate("/");
        return null;
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
