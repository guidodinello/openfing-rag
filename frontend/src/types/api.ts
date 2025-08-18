import z from "zod";

const createApiResponseSchema = <T extends z.ZodTypeAny>(dataSchema: T) =>
    z.object({
        success: z.literal(true),
        message: z.string(),
        data: dataSchema,
    });

const createApiListResponseSchema = <T extends z.ZodTypeAny>(itemSchema: T) =>
    z.object({
        success: z.literal(true),
        message: z.string(),
        data: z.array(itemSchema),
        total: z.number().int().min(0),
    });

export type ApiResponse<T = unknown> = z.infer<
    ReturnType<typeof createApiResponseSchema<z.ZodType<T>>>
>;
export type ApiListResponse<T = unknown> = z.infer<
    ReturnType<typeof createApiListResponseSchema<z.ZodType<T>>>
>;
