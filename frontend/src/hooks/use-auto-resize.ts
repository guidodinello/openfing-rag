import { useEffect, type RefObject } from "react";

interface UseAutoResizeOptions {
    ref: RefObject<HTMLElement | null>;
    trigger: any;
    maxHeight?: number;
    minHeight?: number;
}

export const useAutoResize = ({
    ref,
    trigger,
    maxHeight = 120,
    minHeight = 0,
}: UseAutoResizeOptions) => {
    useEffect(() => {
        const element = ref.current;
        if (!element) return;

        // Reset height to auto to get the correct scrollHeight
        element.style.height = "auto";

        // Calculate new height based on scroll height
        const newHeight = Math.min(element.scrollHeight, maxHeight);

        // Apply minimum height if specified
        const finalHeight = Math.max(newHeight, minHeight);

        element.style.height = `${finalHeight}px`;
    }, [trigger, ref, maxHeight, minHeight]);
};
