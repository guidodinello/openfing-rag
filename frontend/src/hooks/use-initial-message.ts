import { useEffect, useRef } from "react";
import { useLocation } from "react-router";

interface LocationState {
    initialMessage?: string;
}

interface UseInitialMessageOptions {
    onMessage: (message: string) => void;
    enabled?: boolean;
}

export const useInitialMessage = ({
    onMessage,
    enabled = true,
}: UseInitialMessageOptions) => {
    const location = useLocation();
    const processedRef = useRef(false);
    const onMessageRef = useRef(onMessage);
    const prevLocationKey = useRef(location.key);

    useEffect(() => {
        onMessageRef.current = onMessage;
    });

    useEffect(() => {
        // Reset when navigating to a different page/conversation
        if (location.key !== prevLocationKey.current) {
            processedRef.current = false;
            prevLocationKey.current = location.key;
        }

        if (!enabled) return;

        const state = location.state as LocationState;
        const initialMessage = state?.initialMessage;

        if (initialMessage && !processedRef.current) {
            processedRef.current = true;
            onMessageRef.current(initialMessage);

            // Clean up navigation state
            const newState = { ...state };
            delete newState.initialMessage;
            window.history.replaceState(newState, "");
        }
    }, [location.state, location.key, enabled]);
};
