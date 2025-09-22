import { MESSAGE_ROLES } from "@/constants/message-roles";
import z from "zod";
import { sourceSchema } from "./message";

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

const chatResponseSchema = z.object({
    id: z.number().int(),
    answer: z.object({
        modelUsed: z.string(),
        role: z.enum([MESSAGE_ROLES.USER, MESSAGE_ROLES.ASSISTANT]),
        answer: z.string(),
    }),
    sources: z.array(sourceSchema),
    timestamp: z.iso.datetime(),
});

export type ChatResponse = z.infer<typeof chatResponseSchema>;
