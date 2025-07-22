import { z } from "zod";

export const maskApiKey = (key: string): string => {
    if (key.length <= 8) return key;
    return `${key.slice(0, 4)}...${key.slice(-4)}`;
};

export const apiKeySchema = z.object({
    apiKey: z.string().min(1, "API Key es requerida"),
});

export type ApiKeyForm = z.infer<typeof apiKeySchema>;
