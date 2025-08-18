import z from "zod";
import { userSchema } from "./user";
import { timestampSchema } from "./timestamps";
import { messageSchema } from "./message";

const conversationSchema = z.object({
    id: z.int().positive(),
    title: z.string(),
    owner: userSchema,
    ...timestampSchema.shape,
});

export const renameConversationSchema = z.object({
    title: z
        .string()
        .min(1, "El título no puede estar vacío")
        .max(100, "El título no puede exceder 100 caracteres")
        .trim(),
});

const conversationWithMessagesSchema = z.object({
    ...conversationSchema.shape,
    messages: z.array(messageSchema),
});

export type ConversationWithMessages = z.infer<
    typeof conversationWithMessagesSchema
>;
export type Conversation = z.infer<typeof conversationSchema>;
export type RenameConversationForm = z.infer<typeof renameConversationSchema>;
