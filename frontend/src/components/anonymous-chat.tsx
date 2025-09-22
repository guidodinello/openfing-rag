import { useRef } from "react";
import { ChatHeader } from "./chat-header";
import { ChatMessages } from "./chat-messages";
import { ChatInput } from "./chat-input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useScrollToBottom } from "@/hooks/use-scroll";
import { useAnonymousChat } from "@/hooks/use-anonymous-chat";
import { Sparkles } from "lucide-react";
import { useInitialMessage } from "@/hooks/use-initial-message";

export const AnonymousChat = () => {
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const {
        data: messages,
        error,
        isPending,
        mutate: sendMessage,
        sessionId,
    } = useAnonymousChat();

    useScrollToBottom(messagesEndRef, [messages, isPending]);

    const handleSendMessage = (content: string) => {
        if (isPending) return;
        sendMessage({ message: content });
    };

    useInitialMessage({
        onMessage: handleSendMessage,
        enabled: !isPending,
    });

    const hasMessages = messages && messages.length > 0;

    return (
        <div className="flex flex-col h-screen">
            <ChatHeader conversationTitle="Conversación Anónima" />

            <div className="flex-1 flex flex-col min-h-0 mx-auto w-full max-w-4xl px-4 md:px-12 pt-4 pb-8">
                <ScrollArea className="flex-1">
                    {!hasMessages ? (
                        <div className="flex flex-col items-center justify-center h-full p-8 text-center">
                            <div className="size-16 bg-gradient-to-br from-amber-100 to-orange-100 dark:from-amber-900 dark:to-orange-900 rounded-2xl flex items-center justify-center mb-4">
                                <Sparkles className="size-8 text-amber-600 dark:text-amber-400" />
                            </div>
                            <p className="text-muted-foreground max-w-md mb-4">
                                Tu conversación se mantendrá durante esta sesión
                                del navegador.
                            </p>

                            {import.meta.env.DEV && (
                                <div className="mt-4 text-xs text-muted-foreground font-mono">
                                    Session ID: {sessionId}
                                </div>
                            )}
                        </div>
                    ) : (
                        <ChatMessages
                            messages={messages}
                            isLoading={isPending}
                            error={error}
                        />
                    )}
                    <div ref={messagesEndRef} />
                </ScrollArea>

                <div className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                    <div className="p-4">
                        <ChatInput
                            onSendMessage={handleSendMessage}
                            disabled={isPending}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
};
