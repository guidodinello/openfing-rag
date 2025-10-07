import { useEffect } from "react";
import { Icon } from "@/components/icons";
import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useUpdateConversationMutation } from "@/hooks/use-conversation";
import {
    renameConversationSchema,
    type Conversation,
    type RenameConversationForm,
} from "@/types/conversation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { cn } from "@/lib/utils";

interface RenameConversationDialogProps {
    conversation: Conversation | null;
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export const RenameConversationDialog = ({
    conversation,
    open,
    onOpenChange,
}: RenameConversationDialogProps) => {
    const updateConversation = useUpdateConversationMutation();

    const {
        register,
        handleSubmit,
        formState: { errors, isSubmitting },
        reset,
        watch,
    } = useForm<RenameConversationForm>({
        resolver: zodResolver(renameConversationSchema),
        defaultValues: { title: "" },
    });

    const watchedTitle = watch("title");

    useEffect(() => {
        if (open && conversation) {
            reset({ title: conversation.title });
        }
    }, [open, conversation, reset]);

    const onSubmit = (data: RenameConversationForm) => {
        if (!conversation || data.title === conversation.title) {
            onOpenChange(false);
            return;
        }

        updateConversation.mutate(
            {
                conversationId: conversation.id,
                newTitle: data.title,
            },
            {
                onSuccess: () => onOpenChange(false),
            },
        );
    };

    const isLoading = updateConversation.isPending || isSubmitting;

    if (!conversation) return null;

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <Icon.Pencil className="size-4" />
                        Renombrar conversación
                    </DialogTitle>
                    <DialogDescription>
                        Cambia el nombre de tu conversación para identificarla
                        más fácilmente.
                    </DialogDescription>
                </DialogHeader>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="title">Título de la conversación</Label>
                        <Input
                            id="title"
                            type="text"
                            placeholder="Escribe un nuevo título..."
                            {...register("title")}
                            disabled={isLoading}
                            autoFocus
                            className={cn({
                                "border-red-500": errors.title,
                            })}
                        />
                        {errors.title && (
                            <p className="text-sm text-red-500">
                                {errors.title.message}
                            </p>
                        )}
                        <div className="text-xs text-muted-foreground text-right">
                            {watchedTitle.length}/100
                        </div>
                    </div>

                    {updateConversation.error && (
                        <div className="text-sm text-red-500 text-center">
                            Error al renombrar la conversación
                        </div>
                    )}

                    <DialogFooter className="gap-2">
                        <Button
                            type="button"
                            variant="outline"
                            onClick={() => onOpenChange(false)}
                            disabled={isLoading}
                        >
                            Cancelar
                        </Button>
                        <Button type="submit" disabled={isLoading}>
                            {isLoading ? (
                                <>
                                    <Icon.Loader className="size-4 mr-2 animate-spin" />
                                    Guardando...
                                </>
                            ) : (
                                "Guardar cambios"
                            )}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
};
