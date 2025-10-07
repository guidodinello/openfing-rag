import { useParams } from "react-router";

export const useConversationIdParam = (): number | null => {
    const { id } = useParams();

    if (!id) return null;

    const parsed = parseInt(id, 10);
    if (isNaN(parsed) || parsed <= 0) return null;

    return parsed;
};
