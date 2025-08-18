import z from "zod";
import { timestampSchema } from "./timestamps";
import { MESSAGE_ROLES } from "@/constants/message-roles";

const sourceTimestampSchema = z.object({
    start: z.number().int(),
    end: z.number().int(),
});

export const sourceSchema = z.object({
    id: z.string(),
    title: z.string(),
    content: z.string(),
    timestamp: sourceTimestampSchema,
    confidence: z.number(),
    url: z.string(),
});

const baseMessageResponseSchema = z.object({
    id: z.string(),
    content: z.string(),
    ...timestampSchema.shape,
});

const assistantMessageResponseSchema = baseMessageResponseSchema.extend({
    role: z.literal(MESSAGE_ROLES.ASSISTANT),
    sources: z.array(sourceSchema),
});

const userMessageResponseSchema = baseMessageResponseSchema.extend({
    role: z.literal(MESSAGE_ROLES.USER),
});

export const messageSchema = z.union([
    userMessageResponseSchema,
    assistantMessageResponseSchema,
]);

export type SourceTimestamp = z.infer<typeof sourceTimestampSchema>;
export type Source = z.infer<typeof sourceSchema>;

export type AssistantMessage = z.infer<typeof assistantMessageResponseSchema>;
export type UserMessage = z.infer<typeof userMessageResponseSchema>;
export type Message = z.infer<typeof messageSchema>;

const assistantMessageRequestSchema = z.object({
    sessionId: z.uuid(),
    message: z.string().min(1, "Message cannot be empty"),
});

export type AssistantMessageRequest = z.infer<
    typeof assistantMessageRequestSchema
>;
