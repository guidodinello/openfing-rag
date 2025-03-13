export interface ChatMessage {
    text: string;
    isUser: boolean;
    isSources?: boolean;
    isError?: boolean;
}

export interface ChatRequest {
    message: string;
    lesson_id?: number | null;
}

export interface ChatResponse {
    response: string;
    sources: string[];
}
