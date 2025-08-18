import { z } from "zod";

const jwtTokenSchema = z.jwt({ alg: "HS256" });

const bearerTokenResponseSchema = z.object({
    access_token: jwtTokenSchema,
    refresh_token: jwtTokenSchema.optional(),
    token_type: z.literal("bearer"),
});

const registerResponseSchema = z.object({
    id: z.number().int().positive(),
    email: z.email(),
    username: z.string(),
});

export const loginCredentialsSchema = z.object({
    username: z.string(),
    password: z.string(),
});

export type JwtToken = z.infer<typeof jwtTokenSchema>;
export type BearerTokenResponse = z.infer<typeof bearerTokenResponseSchema>;
export type RegisterResponse = z.infer<typeof registerResponseSchema>;
export type LoginCredentials = z.infer<typeof loginCredentialsSchema>;
