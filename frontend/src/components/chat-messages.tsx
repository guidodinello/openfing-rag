import { UserMessage } from "./user-message";
import { AssistantMessage } from "./assistant-message";
import { LoadingMessage } from "./loading-message";
import { ErrorMessage } from "./error-message";
import type { Message } from "@/types/message";

interface ChatMessagesProps {
    readonly messages: Message[];
    readonly isLoading: boolean;
    readonly error?: string | null;
}

export const ChatMessages = ({
    messages,
    isLoading,
    error,
}: ChatMessagesProps) => (
    <div className="space-y-6 py-6">
        {messages.map((message) =>
            message.role === "user" ? (
                <UserMessage key={message.id} message={message} />
            ) : (
                <AssistantMessage key={message.id} message={message} />
            ),
        )}

        {isLoading && <LoadingMessage />}
        {error && <ErrorMessage error={error} />}
    </div>
);
