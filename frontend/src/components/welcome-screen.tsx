import { LuBookOpen } from "react-icons/lu";
import { Card, CardContent } from "@/components/ui/card";
import { useCallback } from "react";
import { useNavigate } from "react-router";
import {
    EXAMPLE_QUESTIONS,
    type ExampleQuestion,
} from "@/constants/example-questions";
import { useConversationCreation } from "@/hooks/use-conversation";
import { ChatInput } from "./chat-input";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth-store";

export const WelcomeScreen = () => {
    const navigate = useNavigate();
    const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
    const { createNewConversation, isCreating } = useConversationCreation();

    const handleExampleClick = useCallback(
        (question: string) => {
            if (isAuthenticated) {
                createNewConversation(question);
            } else {
                navigate("/chat", {
                    state: { initialMessage: question },
                    replace: true,
                });
            }
        },
        [isAuthenticated, createNewConversation, navigate],
    );

    const handleSendMessage = useCallback(
        (message: string) => {
            if (isCreating) return;

            if (isAuthenticated) {
                createNewConversation(message);
            } else {
                navigate("/chat", {
                    state: { initialMessage: message },
                    replace: true,
                });
            }
        },
        [isAuthenticated, createNewConversation, navigate, isCreating],
    );

    return (
        <div className="flex flex-col min-h-[calc(100vh-73px)]">
            <div className="flex-1 flex flex-col items-center justify-center p-4">
                <div className="text-center mb-8">
                    <div className="size-16 bg-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                        <LuBookOpen className="size-8 text-white" />
                    </div>

                    <h2 className="text-2xl font-bold mb-2">
                        ¡Bienvenido al Asistente OpenFIng!
                    </h2>

                    <p className="text-muted-foreground max-w-md mx-auto">
                        Pregúntame sobre cualquier tema de las clases de
                        OpenFIng. Puedo ayudarte con programación, algoritmos,
                        matemáticas y más.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-2xl">
                    {EXAMPLE_QUESTIONS.map((question) => (
                        <ExampleQuestionCard
                            key={question.text}
                            question={question}
                            onClick={handleExampleClick}
                            disabled={isCreating}
                        />
                    ))}
                </div>
            </div>

            <div className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                <div className="max-w-4xl mx-auto px-4 py-4">
                    <ChatInput
                        onSendMessage={handleSendMessage}
                        disabled={isCreating}
                    />
                </div>
            </div>
        </div>
    );
};

interface ExampleQuestionCardProps {
    question: ExampleQuestion;
    onClick: (question: string) => void;
    disabled?: boolean;
}

const ExampleQuestionCard = ({
    question,
    onClick,
    disabled = false,
}: ExampleQuestionCardProps) => {
    const Icon = question.icon;

    return (
        <Card
            className={cn(
                "hover:shadow-md hover:border-blue-200 dark:hover:border-blue-800 transition-all duration-200 group cursor-pointer",
                {
                    "opacity-50 cursor-not-allowed": disabled,
                },
            )}
            onClick={() => !disabled && onClick(question.text)}
        >
            <CardContent className="p-4">
                <div className="flex items-start gap-3">
                    <div className="size-8 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:bg-blue-200 dark:group-hover:bg-blue-800 transition-colors">
                        <Icon className="size-4 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                        <div className="text-xs font-medium text-blue-600 dark:text-blue-400 mb-1.5">
                            {question.category}
                        </div>
                        <p className="text-sm font-medium leading-relaxed text-foreground">
                            {question.text}
                        </p>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
};
