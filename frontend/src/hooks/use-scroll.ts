import { useEffect, type RefObject } from "react";

export const useScrollToBottom = (
    ref: RefObject<HTMLElement | null>,
    dependency?: unknown[],
) => {
    useEffect(() => {
        if (ref.current) {
            const timeoutId = setTimeout(() => {
                ref.current?.scrollIntoView({ behavior: "smooth" });
            }, 100);

            return () => clearTimeout(timeoutId);
        }
    }, [ref, ...(dependency || [])]);
};
