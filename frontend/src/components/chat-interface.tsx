import { useState, useRef, useEffect } from "react";
import { ChatHeader } from "./chat-header";
import { ChatMessages } from "./chat-messages";
import { ChatInput } from "./chat-input";
import { WelcomeScreen } from "./welcome-screen";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useChatMutation } from "@/hooks/use-chat";

export const ChatInterface = () => {
    const [sessionId] = useState(() => crypto.randomUUID());
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const { messages, sendMessage, isLoading, error } =
        useChatMutation(sessionId);

    useEffect(() => {
        const scrollToBottom = () => {
            messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
        };
        scrollToBottom();
    }, [messages]);

    const handleSendMessage = (content: string) => {
        sendMessage(content);
    };

    return (
        <div className="flex flex-col h-screen mx-auto px-12 pt-4 pb-8">
            <ChatHeader />

            <div className="flex-1 flex flex-col min-h-0">
                <ScrollArea className="flex-1 px-4">
                    {messages.length === 0 ? (
                        <WelcomeScreen onExampleClick={handleSendMessage} />
                    ) : (
                        <ChatMessages
                            messages={messages}
                            isLoading={isLoading}
                            error={error}
                        />
                    )}
                    <div ref={messagesEndRef} />
                </ScrollArea>

                <div className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                    <div className="px-4 py-4">
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
