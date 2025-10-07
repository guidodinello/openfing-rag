import { Icon } from "@/components/icons";
import { Button } from "@/components/ui/button";
import { SourceCitations } from "./source-citations";
import type { AssistantMessage as AssistantMessageType } from "@/types/message";
import { formatToLocalTime } from "@/utils/dates";
import { useCopyToClipboard } from "@/hooks/use-copy-to-clipboard";
import { RichText } from "./rich-text";

interface AssistantMessageProps {
    readonly message: AssistantMessageType;
}

export const AssistantMessage = ({ message }: AssistantMessageProps) => {
    const { copied, handleCopy } = useCopyToClipboard(message.content);

    return (
        <div className="flex gap-3 group flex-col md:flex-row">
            <div className="flex-shrink-0 size-8 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mt-1">
                <Icon.Bot className="size-4 text-green-600 dark:text-green-400" />
            </div>

            <div className="flex-1 max-w-[80vw] md:max-w-[70vh]">
                <div className="bg-muted rounded-2xl rounded-tl-md px-4 py-3 relative">
                    <RichText content={message.content} variant="assistant" />

                    <Button
                        variant="ghost"
                        size="icon"
                        className="absolute -top-2 -right-2 opacity-0 group-hover:opacity-100 transition-opacity bg-background border shadow-sm hover:bg-accent size-8"
                        onClick={handleCopy}
                    >
                        {copied ? (
                            <Icon.Check className="size-3 text-green-600" />
                        ) : (
                            <Icon.Copy className="size-3" />
                        )}
                    </Button>
                </div>

                {message.sources && message.sources.length > 0 && (
                    <div className="mt-3">
                        <SourceCitations sources={message.sources} />
                    </div>
                )}

                <div className="mt-1">
                    <span className="text-xs text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">
                        {formatToLocalTime(new Date(message.updated_at))}
                    </span>
                </div>
            </div>
        </div>
    );
};
