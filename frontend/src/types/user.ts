import z from "zod";

export const userSchema = z.object({
    id: z.number().int().positive(),
    email: z.email(),
    username: z.string(),
});

export type User = z.infer<typeof userSchema>;
