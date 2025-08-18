import type React from "react";

import { useState, useRef, useEffect, forwardRef } from "react";
import { LuSend } from "react-icons/lu";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { cn } from "@/lib/utils";

const messageSchema = z.object({
    message: z
        .string()
        .trim()
        .min(1, "El mensaje no puede estar vacío")
        .max(1000, "El mensaje es demasiado largo"),
});

type MessageForm = z.infer<typeof messageSchema>;

interface ChatInputProps {
    readonly onSendMessage: (message: string) => void;
    readonly disabled?: boolean;
}

const ForwardedTextarea = forwardRef<
    HTMLTextAreaElement,
    React.ComponentProps<typeof Textarea>
>(({ ...props }, ref) => {
    return <Textarea ref={ref} {...props} />;
});

ForwardedTextarea.displayName = "ForwardedTextarea";

// TODO: use shadcn form
export const ChatInput = ({ onSendMessage, disabled }: ChatInputProps) => {
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const [charCount, setCharCount] = useState(0);

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

    useEffect(() => {
        setCharCount(message?.length || 0);
    }, [message]);

    // Auto-resize textarea
    useEffect(() => {
        const textarea = textareaRef.current;
        if (textarea) {
            textarea.style.height = "auto";
            textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
        }
    }, [message]);

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
            handleSubmit(onSubmit)();
        }
    };

    return (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-2">
            <div className="relative flex  ">
                <div className="flex flex-col items-center justify-center w-full">
                    <Controller
                        name="message"
                        control={control}
                        render={({ field: { value, ...rest } }) => (
                            <ForwardedTextarea
                                {...rest}
                                ref={textareaRef}
                                value={value || ""}
                                placeholder="Pregunta sobre las clases de OpenFIng..."
                                className="resize-none pr-24 py-3 flex-grow w-full overflow-hidden leading-tight min-h-[44px]"
                                disabled={disabled}
                                onKeyDown={handleKeyDown}
                                rows={1}
                            />
                        )}
                    />
                </div>
                <div className="absolute right-2">
                    <Button
                        type="submit"
                        size="icon"
                        className="size-8"
                        disabled={disabled || !isValid}
                        title="Enviar mensaje"
                    >
                        <LuSend className="size-4" />
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
                            holas Presiona Enter para enviar, Shift+Enter para
                            nueva línea
                        </span>
                    )}
                </div>

                <span className={cn(charCount > 900 && "text-orange-500")}>
                    {charCount}/1000
                </span>
            </div>
        </form>
    );
};
