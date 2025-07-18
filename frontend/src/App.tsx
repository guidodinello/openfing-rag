import { ChatInterface } from "@/components/chat-interface";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "./components/theme-provider";

const FIVE_MINUTES = 1000 * 60 * 5;
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: FIVE_MINUTES,
            retry: 2,
        },
    },
});

const App = () => (
    <QueryClientProvider client={queryClient}>
        <ThemeProvider
            attribute="class"
            defaultTheme="light"
            enableSystem
            disableTransitionOnChange
        >
            <div className="min-h-screen bg-background">
                <ChatInterface />
            </div>
        </ThemeProvider>
    </QueryClientProvider>
);

export default App;
