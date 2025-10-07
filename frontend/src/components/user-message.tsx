import { Icon } from "@/components/icons";
import { Button } from "@/components/ui/button";
import { formatToLocalTime } from "@/utils/dates";
import { useCopyToClipboard } from "@/hooks/use-copy-to-clipboard";
import type { UserMessage as UserMessageType } from "@/types/message";
import { RichText } from "./rich-text";

interface UserMessageProps {
    readonly message: UserMessageType;
}

export const UserMessage = ({ message }: UserMessageProps) => {
    const { copied, handleCopy } = useCopyToClipboard(message.content);

    return (
        <div className="flex justify-end group">
            <div className="max-w-[80%] md:max-w-[70%]">
                <div className="bg-blue-600  rounded-2xl rounded-tr-md px-4 py-3 relative">
                    <RichText content={message.content} variant="user" />

                    <Button
                        variant="ghost"
                        size="icon"
                        className="absolute -top-2 -left-2 opacity-0 group-hover:opacity-100 transition-opacity bg-background border shadow-sm hover:bg-accent size-8"
                        onClick={handleCopy}
                    >
                        {copied ? (
                            <Icon.Check className="size-3 text-green-600" />
                        ) : (
                            <Icon.Copy className="size-3" />
                        )}
                    </Button>
                </div>

                <div className="flex justify-end mt-1">
                    <span className="text-xs text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">
                        {formatToLocalTime(new Date(message.updated_at))}
                    </span>
                </div>
            </div>
        </div>
    );
};
