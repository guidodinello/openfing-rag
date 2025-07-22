import z from "zod";
import { sourceSchema } from "./types";

// ENDPOINT SCHEMAS AND TYPES

const baseMessageResponseSchema = z.object({
    id: z.string(),
    content: z.string(),
    timestamp: z.date(),
});

const assistantMessageResponseSchema = baseMessageResponseSchema.extend({
    role: z.literal("assistant"),
    sources: z.array(sourceSchema),
});

const userMessageResponseSchema = baseMessageResponseSchema.extend({
    role: z.literal("user"),
});

const assistantMessageRequestSchema = z.object({
    sessionId: z.uuid(),
    message: z.string().min(1, "Message cannot be empty"),
});

export type AssistantMessageRequest = z.infer<
    typeof assistantMessageRequestSchema
>;

export type AssistantMessage = z.infer<typeof assistantMessageResponseSchema>;
export type UserMessage = z.infer<typeof userMessageResponseSchema>;
export type Message = UserMessage | AssistantMessage;

export type Optimistic<T> = T & {
    isOptimistic: true;
};

export const isOptimistic = <T>(
    item: T | Optimistic<T>,
): item is Optimistic<T> => {
    return (
        typeof item === "object" &&
        item !== null &&
        "isOptimistic" in item &&
        item.isOptimistic === true
    );
};
