import { LuCircleAlert, LuRefreshCw } from "react-icons/lu";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface ErrorMessageProps {
    readonly error: string;
    readonly onRetry?: () => void;
}

export const ErrorMessage = ({ error, onRetry }: ErrorMessageProps) => {
    return (
        <Alert variant="destructive" className="max-w-[80%] md:max-w-[70%]">
            <LuCircleAlert className="h-4 w-4" />
            <AlertDescription className="flex items-center justify-between">
                <span>{error}</span>
                {onRetry && (
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={onRetry}
                        className="ml-2 bg-transparent"
                    >
                        <LuRefreshCw className="size-3 mr-1" />
                        Reintentar
                    </Button>
                )}
            </AlertDescription>
        </Alert>
    );
};
