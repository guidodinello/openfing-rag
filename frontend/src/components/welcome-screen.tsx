import { LuBookOpen } from "react-icons/lu";
import { Card, CardContent } from "@/components/ui/card";
import { EXAMPLE_QUESTIONS, type ExampleQuestion } from "@/constants";

interface WelcomeScreenProps {
    readonly onExampleClick: (question: string) => void;
}

export function WelcomeScreen({ onExampleClick }: WelcomeScreenProps) {
    return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] p-4">
            <div className="text-center mb-8">
                <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <LuBookOpen className="size-8 text-white" />
                </div>

                <h2 className="text-2xl font-bold mb-2">
                    ¡Bienvenido al Asistente OpenFIng!
                </h2>

                <p className="text-muted-foreground max-w-md mx-auto">
                    Pregúntame sobre cualquier tema de las clases de OpenFIng.
                    Puedo ayudarte con programación, algoritmos, matemáticas y
                    más.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-2xl">
                {EXAMPLE_QUESTIONS.map((question) => (
                    <ExampleQuestionCard
                        key={question.text}
                        question={question}
                        onClick={onExampleClick}
                        // should be a navigate to another screen?
                    />
                ))}
            </div>
        </div>
    );
}

interface ExampleQuestionCardProps {
    question: ExampleQuestion;
    onClick: (question: string) => void;
}

const ExampleQuestionCard = ({
    question,
    onClick: onExampleClick,
}: ExampleQuestionCardProps) => {
    const Icon = question.icon;
    return (
        <Card
            className="hover:shadow-md hover:border-blue-200 dark:hover:border-blue-800 transition-all duration-200 group"
            onClick={() => onExampleClick(question.text)}
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
