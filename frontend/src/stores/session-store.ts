import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

const SESSION_ID_PATTERN = /^anon_[A-Za-z0-9_-]{16,32}_\d{10}$/;

export type SessionId = string;

const isValidSessionId = (sessionId: string): boolean => {
    return SESSION_ID_PATTERN.test(sessionId);
};

const generateSessionId = (): SessionId => {
    return `anon_${crypto.randomUUID().replace(/-/g, "").substring(0, 16)}_${Math.floor(Date.now() / 1000)}`;
};

interface SessionState {
    sessionId: SessionId;
}

interface SessionActions {
    setSessionId: (sessionId: SessionId) => void;
    clearSession: () => void;
}

export const useSessionStore = create<SessionState & SessionActions>()(
    persist(
        (set) => ({
            sessionId: generateSessionId(),

            setSessionId: (sessionId) => {
                if (isValidSessionId(sessionId)) {
                    console.log(
                        "[SessionStore] Setting session ID:",
                        sessionId,
                    );
                    set({ sessionId });
                }
            },

            clearSession: () => {
                console.log("[SessionStore] Clearing session");
                set({ sessionId: generateSessionId() });
            },
        }),
        {
            name: "anonymous-chat-session",
            storage: createJSONStorage(() => sessionStorage),
        },
    ),
);
