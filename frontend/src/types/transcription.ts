import { z } from "zod";

export const modelSizeSchema = z.enum([
    "tiny",
    "base",
    "small",
    "medium",
    "large",
]);

// Main transcription schema
export const transcriptionSchema = z.object({
    id: z.number().int().positive(),
    lesson_id: z.number().int().positive(),
    course_id: z.number().int().positive(),
    transcriber: z.object({
        identifier: z.string(),
        size: modelSizeSchema,
    }),
    lesson_title: z.string(),
    content: z.string(),
    content_length: z.number().int().nonnegative(),
});

export type ModelSize = z.infer<typeof modelSizeSchema>;
export type Transcription = z.infer<typeof transcriptionSchema>;
