import { useParams } from "react-router";
import z from "zod";

const conversationIdParamSchema = z.object({
    id: z.string().transform((val) => {
        const num = Number(val);
        if (Number.isNaN(num) || num <= 0) {
            throw new Error("Invalid conversation ID");
        }
        return num;
    }),
});

export type ConversationIdParam = {
    conversationId: number;
};

export const useConversationIdParam = (): ConversationIdParam | null => {
    const params = useParams<{ conversationId: string }>();

    const result = conversationIdParamSchema.safeParse(params);
    if (!result.success) {
        return null;
    }
    return { conversationId: result.data.id };
};
