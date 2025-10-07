import type React from "react";

import { useRef } from "react";
import { Icon } from "@/components/icons";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { cn } from "@/lib/utils";
import { useAutoResize } from "@/hooks/use-auto-resize";

const messageSchema = z.object({
    message: z
        .string()
        .trim()
        .min(1, "El mensaje no puede estar vacío")
        .max(1000, "El mensaje es demasiado largo"),
});

type Message = z.infer<typeof messageSchema>;
type MessageForm = Message;

interface ChatInputProps {
    readonly onSendMessage: (message: string) => void;
    readonly disabled?: boolean;
}

const ForwardedTextarea = ({
    ref,
    ...props
}: React.ComponentProps<typeof Textarea> & {
    ref?: React.Ref<HTMLTextAreaElement>;
}) => {
    return <Textarea ref={ref} {...props} />;
};

// TODO: use shadcn form
export const ChatInput = ({ onSendMessage, disabled }: ChatInputProps) => {
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const {
        control,
        handleSubmit,
        reset,
        watch,
        formState: { errors, isValid },
    } = useForm<MessageForm>({
        resolver: zodResolver(messageSchema),
        defaultValues: { message: "" },
        mode: "onChange",
    });

    const message = watch("message");

    useAutoResize({
        ref: textareaRef,
        trigger: message,
        maxHeight: 120,
    });

    const onSubmit = (data: MessageForm) => {
        const msg = data.message.trim();
        if (!disabled && msg) {
            onSendMessage(msg);
            reset();
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            void handleSubmit(onSubmit)();
        }
    };

    return (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-2">
            <div className="relative flex items-center justify-center">
                <Controller
                    name="message"
                    control={control}
                    render={({ field: { value, ...rest } }) => (
                        <ForwardedTextarea
                            {...rest}
                            ref={textareaRef}
                            value={value || ""}
                            placeholder="Pregunta sobre las clases de OpenFIng..."
                            className="resize-none pr-24 py-3 flex-grow w-full overflow-hidden leading-tight min-h-16 md:min-h-11"
                            disabled={disabled}
                            onKeyDown={handleKeyDown}
                            rows={1}
                        />
                    )}
                />

                <div className="absolute right-2">
                    <Button
                        type="submit"
                        size="icon"
                        className="size-8"
                        disabled={disabled ?? !isValid}
                        title="Enviar mensaje"
                    >
                        <Icon.Send className="size-4" />
                    </Button>
                </div>
            </div>

            <div className="flex items-center justify-between text-xs text-muted-foreground">
                <div className="flex items-center gap-4">
                    {errors.message ? (
                        <span className="text-red-500">
                            {errors.message.message}
                        </span>
                    ) : (
                        <span className="hidden sm:inline">
                            Presiona Enter para enviar, Shift+Enter para nueva
                            línea
                        </span>
                    )}
                </div>

                <CharCounter message={message} />
            </div>
        </form>
    );
};

const CharCounter = ({ message }: Message) => {
    const charCount = message?.length ?? 0;

    return (
        <span className={cn(charCount > 900 && "text-orange-500")}>
            {charCount}/1000
        </span>
    );
};
