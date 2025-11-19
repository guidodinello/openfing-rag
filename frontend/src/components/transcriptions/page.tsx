import { useEffect } from "react";
import { useNavigate } from "react-router";
import { isAxiosError } from "axios";
import { useTranscriptionQuery } from "@/hooks/use-transcription";
import { TranscriptionViewer } from "@/components/transcriptions/viewer";
import { LoadingMessage } from "@/components/loading-message";
import { ErrorMessage } from "@/components/error-message";
import type { TranscriptionParams } from "@/hooks/use-transcription-params";

export const TranscriptionPage = ({
    courseCode,
    lessonNumber,
    modelSize,
}: TranscriptionParams) => {
    const navigate = useNavigate();
    const { data, isLoading, error, refetch } = useTranscriptionQuery({
        courseCode,
        lessonNumber,
        modelSize,
    });

    useEffect(() => {
        if (error && !isLoading) {
            if (isAxiosError(error)) {
                const status = error.response?.status;
                if (status === 404 || status === 401 || status === 403) {
                    void navigate("/", { replace: true });
                }
            }
        }
    }, [error, isLoading, navigate]);

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[80vh] p-4">
                <LoadingMessage />
                <p className="text-muted-foreground mt-4">
                    Cargando transcripción...
                </p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[80vh] p-4">
                <ErrorMessage
                    error={
                        error instanceof Error
                            ? error.message
                            : "Error al cargar la transcripción"
                    }
                    onRetry={() => refetch()}
                />
            </div>
        );
    }

    if (!data) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[80vh] p-4">
                <p className="text-muted-foreground">
                    No se encontró la transcripción
                </p>
            </div>
        );
    }

    return <TranscriptionViewer transcription={data} />;
};
