import { z, type ZodType } from "zod";

export const createJsonStringParser = <T extends ZodType>(schema: T) =>
    z.string().pipe(
        z.preprocess((input, ctx) => {
            if (typeof input !== "string") {
                ctx.addIssue({
                    code: "custom",
                    message: "Expected string",
                    path: [],
                });
                return z.NEVER;
            }

            try {
                return JSON.parse(input) as unknown;
            } catch (error) {
                ctx.addIssue({
                    code: "custom",
                    message: `Invalid JSON - ${(error as Error).message}`,
                    path: [],
                });
                return z.NEVER;
            }
        }, schema),
    );
