import { ChatInterface } from "@/components/chat-interface";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "./components/theme-provider";
import { MINS_5, SECONDS_2, SECONDS_30 } from "./constants/time";
import { SidebarProvider } from "./components/ui/sidebar";
import { Routes, Route, Navigate } from "react-router";
import { Layout } from "./components/layout";
import { WelcomeScreen } from "./components/welcome-screen";
import { HttpStatusCode, isAxiosError } from "axios";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AnonymousChat } from "@/components/anonymous-chat";
import { useRefreshToken } from "@/hooks/use-refresh-token";
import { ParamGuard } from "@/components/route-guards/param-guard";
import { useConversationIdParam } from "./hooks/use-conversation-id-param";
import { TranscriptionPage } from "@/components/transcriptions/page";
import { useTranscriptionParams } from "./hooks/use-transcription-params";

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: MINS_5,
            retry: (failureCount, error) => {
                if (!isAxiosError(error)) return false;

                const status = error.response?.status;

                if (!status) return failureCount < 3;

                // Server Errors (5xx)
                if (status >= 500) return failureCount < 3;

                if (status === (HttpStatusCode.TooManyRequests as number))
                    return failureCount < 2;

                // Client Errors (4xx)
                if (status >= 400 && status < 500) return false;

                return false;
            },
            retryDelay: (attemptIndex) =>
                Math.min(SECONDS_2 ** attemptIndex, SECONDS_30),
        },
    },
});

const Router = () => (
    <Routes>
        <Route
            path="/conversation/:id"
            element={
                <ParamGuard useParam={useConversationIdParam}>
                    {(params) => (
                        <ChatInterface conversationId={params.conversationId} />
                    )}
                </ParamGuard>
            }
        />
        <Route
            path="/transcription/:courseCode/lesson/:lessonNumber/:modelSize?"
            element={
                <ParamGuard useParam={useTranscriptionParams}>
                    {(params) => (
                        <TranscriptionPage
                            courseCode={params.courseCode}
                            lessonNumber={params.lessonNumber}
                            modelSize={params.modelSize}
                        />
                    )}
                </ParamGuard>
            }
        />
        <Route path="/chat" element={<AnonymousChat />} />
        <Route path="/" element={<WelcomeScreen />} />
        <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
);

const AppContent = () => {
    useRefreshToken();

    return (
        <ThemeProvider
            attribute="class"
            defaultTheme="light"
            enableSystem
            disableTransitionOnChange
        >
            <TooltipProvider>
                <SidebarProvider>
                    <Toaster position="top-center" />
                    <Layout>
                        <Router />
                    </Layout>
                </SidebarProvider>
            </TooltipProvider>
        </ThemeProvider>
    );
};

const App = () => (
    <QueryClientProvider client={queryClient}>
        <AppContent />
    </QueryClientProvider>
);

export default App;
