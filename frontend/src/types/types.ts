import { z } from "zod";

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

const chatAnswerSchema = z.object({
    id: z.string(),
    timestamp: z.iso.date(),
    content: z.string(),
    sources: z.array(sourceSchema),
});

export type ChatAnswer = z.infer<typeof chatAnswerSchema>;
export type Source = z.infer<typeof sourceSchema>;
export type SourceTimestamp = z.infer<typeof sourceTimestampSchema>;
