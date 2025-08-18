import { z } from "zod";
import { createJsonStringParser } from "./json-parser";

const JWTPayloadSchema = z.object({
    sub: z.string(),
    user_id: z.number(),
    exp: z.number(),
    iat: z.number(),
    type: z.enum(["access", "refresh"]),
});

const jwtPayloadParser = createJsonStringParser(JWTPayloadSchema);

type JWTPayload = z.infer<typeof JWTPayloadSchema>;

export const decodeJWTPayload = (token: string): JWTPayload | null => {
    try {
        const parts = token.split(".");
        if (parts.length !== 3) return null;

        const base64Url = parts[1];
        const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");

        const jsonPayload = decodeURIComponent(
            atob(base64)
                .split("")
                .map(
                    (c) =>
                        "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2),
                )
                .join(""),
        );

        const result = jwtPayloadParser.safeParse(jsonPayload);
        return result.success ? result.data : null;
    } catch (error) {
        console.error("Error decoding JWT:", error);
        return null;
    }
};

export const isJWTExpired = (token: string): boolean => {
    const payload = decodeJWTPayload(token);
    if (!payload?.exp) return true;

    return Date.now() >= payload.exp * 1000;
};

export const getTokenClaims = (token: string): JWTPayload | null => {
    return decodeJWTPayload(token);
};
