import {
    getTranscription,
    type GetTranscriptionParams,
} from "@/api/transcription";
import { useQuery } from "@tanstack/react-query";
import { MINS_5 } from "@/constants/time";

export const useTranscriptionQuery = ({
    courseCode,
    lessonNumber,
    modelSize,
}: GetTranscriptionParams) => {
    return useQuery({
        queryKey: ["transcription", courseCode, lessonNumber, modelSize],
        queryFn: () =>
            getTranscription({ courseCode, lessonNumber, modelSize }),
        enabled: !!courseCode && !!lessonNumber,
        staleTime: MINS_5,
    });
};

export const transcriptionKeys = {
    all: ["transcription"] as const,
    detail: (courseCode: string, lessonNumber: number, modelSize: string) =>
        [
            ...transcriptionKeys.all,
            courseCode,
            lessonNumber,
            modelSize,
        ] as const,
    course: (courseCode: string) =>
        [...transcriptionKeys.all, courseCode] as const,
};
