import { useRef, useEffect, useState, useCallback } from "react";
import { useLocation, useNavigate } from "react-router";
import { ChatHeader } from "./chat-header";
import { ChatMessages } from "./chat-messages";
import { ChatInput } from "./chat-input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useChatMutation } from "@/hooks/use-chat";
import { useConversationQuery } from "@/hooks/use-conversation";
import { LoadingMessage } from "./loading-message";
import { useConversationIdParam } from "@/hooks/use-conversation-id-param";
import { useScrollToBottom } from "@/hooks/use-scroll";

export const ChatInterface = () => {
    const { id } = useConversationIdParam();
    const location = useLocation();
    const navigate = useNavigate();
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const [initialMessageProcessed, setInitialMessageProcessed] =
        useState(false);

    const {
        data: conversation,
        isLoading: isLoadingConversation,
        error: conversationError,
    } = useConversationQuery(id);

    const { messages, sendMessage, isLoading, error } = useChatMutation(id);

    useScrollToBottom(messagesEndRef, [messages.length, isLoading]);

    const initialMessage = location.state?.initialMessage as string | undefined;

    const handleSendMessage = useCallback(
        (content: string) => {
            if (isLoading) return;
            sendMessage(content);
        },
        [sendMessage, isLoading],
    );

    useEffect(() => {
        if (
            initialMessage &&
            !initialMessageProcessed &&
            conversation &&
            messages.length === 0 &&
            !isLoading &&
            !isLoadingConversation
        ) {
            setInitialMessageProcessed(true);
            handleSendMessage(initialMessage);

            const newState = { ...location.state };
            delete newState.initialMessage;
            window.history.replaceState(newState, "");
        }
    }, [
        initialMessage,
        initialMessageProcessed,
        conversation,
        messages.length,
        isLoading,
        isLoadingConversation,
        handleSendMessage,
        location.state,
    ]);

    // TODO: i dont like this, remove
    useEffect(() => {
        setInitialMessageProcessed(false);
    }, [id]);

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
