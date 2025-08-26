import { isValidationError } from "@/utils/errors";
import type { UseMutationResult } from "@tanstack/react-query";

interface ValidationErrorProps {
    field: string;
    errors: string[];
}

const ValidationError = ({ field, errors }: ValidationErrorProps) => (
    <div key={field} className="text-sm text-red-500 text-center">
        {errors.map((msg, index) => (
            <div key={index}>{msg}</div>
        ))}
    </div>
);

interface FormMutationErrorsProps<
    /* eslint-disable @typescript-eslint/no-explicit-any */
    TData = any,
    TError = unknown,
    TVariables = any,
    TContext = unknown,
    /* eslint-enable @typescript-eslint/no-explicit-any */
> {
    mutation: UseMutationResult<TData, TError, TVariables, TContext>;
}

export const FormMutationErrors = <TData, TError, TVariables, TContext>({
    mutation,
}: FormMutationErrorsProps<TData, TError, TVariables, TContext>) => {
    if (isValidationError(mutation.error)) {
        const errors = mutation.error.response?.data?.errors ?? {};

        return (
            <div className="space-y-2">
                {Object.entries(errors).map(([field, messages]) => (
                    <ValidationError
                        key={field}
                        field={field}
                        errors={messages}
                    />
                ))}
            </div>
        );
    }

    return null;
};
