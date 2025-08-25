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
    username: z.string().min(1, "Username is required"),
    password: z.string().min(1, "Password is required"),
});

export const registerCredentialsSchema = z
    .object({
        email: z.string().email("Please enter a valid email address"),
        username: z
            .string()
            .min(3, "Username must be at least 3 characters long")
            .max(30, "Username must be less than 30 characters")
            .regex(
                /^[a-zA-Z0-9_-]+$/,
                "Username can only contain letters, numbers, hyphens, and underscores",
            ),
        password: z
            .string()
            .min(8, "Password must be at least 8 characters long")
            .regex(
                /[A-Z]/,
                "Password must contain at least one uppercase letter",
            )
            .regex(
                /[a-z]/,
                "Password must contain at least one lowercase letter",
            )
            .regex(/\d/, "Password must contain at least one number"),
        confirmPassword: z.string().min(1, "Please confirm your password"),
    })
    .refine((data) => data.password === data.confirmPassword, {
        message: "Passwords don't match",
        path: ["confirmPassword"],
    });

export type JwtToken = z.infer<typeof jwtTokenSchema>;
export type BearerTokenResponse = z.infer<typeof bearerTokenResponseSchema>;
export type RegisterResponse = z.infer<typeof registerResponseSchema>;
export type LoginCredentials = z.infer<typeof loginCredentialsSchema>;
export type RegisterCredentials = z.infer<typeof registerCredentialsSchema>;
