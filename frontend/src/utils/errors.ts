import {
    validationErrorSchema,
    type ValidationErrorResponse,
} from "@/types/api";
import type { AxiosError } from "axios";
import { isAxiosError } from "axios";
export const isValidationError = (
    error: unknown,
): error is AxiosError<ValidationErrorResponse> => {
    if (!isAxiosError(error)) return false;
    if (!error.response?.data) return false;

    const parsed = validationErrorSchema.safeParse(error.response.data);

    return parsed.success;
};
