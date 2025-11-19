import { useParams } from "react-router";
import z from "zod";
import { modelSizeSchema } from "@/types/transcription";

const transcriptionParamsSchema = z.object({
    courseCode: z.string().min(1),
    lessonNumber: z.string().transform((val) => {
        const num = Number(val);
        if (Number.isNaN(num) || num <= 0 || !Number.isInteger(num)) {
            throw new Error("Invalid lesson number");
        }
        return num;
    }),
    modelSize: z
        .string()
        .optional()
        .transform((val) => {
            if (!val) return undefined;
            const result = modelSizeSchema.safeParse(val);
            if (!result.success) {
                throw new Error("Invalid model size");
            }
            return result.data;
        }),
});

export type TranscriptionParams = {
    courseCode: string;
    lessonNumber: number;
    modelSize?: z.infer<typeof modelSizeSchema>;
};

export const useTranscriptionParams = (): TranscriptionParams | null => {
    const params = useParams<{
        courseCode: string;
        lessonNumber: string;
        modelSize?: string;
    }>();

    const result = transcriptionParamsSchema.safeParse(params);
    if (!result.success) {
        return null;
    }
    return result.data;
};
