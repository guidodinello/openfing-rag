import type {
    AssistantMessageRequest,
    Message,
    AssistantMessage,
} from "@/types/chat";
import { privateApiClient } from "./axios";

export const sendMessage = async (data: AssistantMessageRequest) => {
    const response = await privateApiClient.post<AssistantMessage>(
        "/generator/chat",
        data,
    );
    return response.data;
};

export const getMessages = async (_: string) => {
    return [] satisfies Message[];

    // return [
    //     {
    //         id: "1",
    //         role: "assistant",
    //         content: "Hello! How can I assist you today?",
    //         timestamp: new Date(),
    //         sources: [],
    //     },
    // ] satisfies Message[];
};
