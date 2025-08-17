import type { FilteringType } from "./filter";

export type MessageSender = "user" | "chatbot";

export interface Message {
    messageSender: MessageSender;
    text: string;
    filteringType: FilteringType;
    filterOptions;
}
