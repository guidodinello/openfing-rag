import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router";

const asInteger = (value: string | undefined): number | never => {
    if (!value) throw new Error("Value is undefined");

    const parsed = parseInt(value, 10);
    if (isNaN(parsed)) throw new Error("Value is not a number");
    if (parsed <= 0) throw new Error("Value must be positive");

    return parsed;
};

const useValidatedParam = <T>(
    paramName: string,
    parser: (value: string | undefined) => T,
    redirectTo: string = "/",
): T => {
    const params = useParams();
    const navigate = useNavigate();
    const paramValue = params[paramName];
    const [validated, setValidated] = useState<T | null>(null);

    useEffect(() => {
        try {
            const result = parser(paramValue);
            setValidated(result);
        } catch (error) {
            console.warn(
                `Invalid URL parameter ${paramName}: ${paramValue}`,
                error,
            );
            navigate(redirectTo, { replace: true });
        }
    }, [paramValue, paramName, redirectTo, navigate, parser]);

    return validated as T;
};

export const useConversationIdParam = () => ({
    id: useValidatedParam("id", asInteger),
});
