import { type ReactNode } from "react";
import { Navigate } from "react-router";

interface ParamGuardProps<T> {
    useParam: () => T | null;
    children: (value: T) => ReactNode;
    redirectTo?: string;
}

export const ParamGuard = <T,>({
    useParam,
    children,
    redirectTo = "/",
}: ParamGuardProps<T>) => {
    const value = useParam();

    if (value === null) {
        return <Navigate to={redirectTo} replace />;
    }

    return <>{children(value)}</>;
};
