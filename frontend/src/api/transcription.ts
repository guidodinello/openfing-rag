import type { ModelSize, Transcription } from "@/types/transcription";
import { transcriptionSchema } from "@/types/transcription";
import { privateApiClient } from "./axios";
import type { ApiResponse } from "@/types/api";

export interface GetTranscriptionParams {
    courseCode: string;
    lessonNumber: number;
    modelSize?: ModelSize;
}

export const getTranscription = async ({
    courseCode,
    lessonNumber,
    modelSize = "medium",
}: GetTranscriptionParams): Promise<Transcription> => {
    const params = new URLSearchParams({ modelSize });

    const response = await privateApiClient.get<ApiResponse<Transcription>>(
        `/courses/${courseCode}/lessons/${lessonNumber}?${params.toString()}`,
    );

    return transcriptionSchema.parse(response.data.data);
};

export const getTranscriptionById = async (
    id: number,
): Promise<Transcription> => {
    const response = await privateApiClient.get<ApiResponse<Transcription>>(
        `/transcriptions/${id}`,
    );

    return transcriptionSchema.parse(response.data.data);
};
