import { useNavigate } from "react-router";
import { Logo } from "./logo";
import { AppHeader } from "./app-header";
import { ThemeToggle } from "./theme-toggle";
import { ProfileDialog } from "./profile-dialog";
import { SidebarTrigger } from "./ui/sidebar";
import { useAuthStore } from "@/stores/auth-store";

interface ChatHeaderProps {
    readonly conversationTitle?: string;
}

export const ChatHeader = ({ conversationTitle }: ChatHeaderProps) => {
    const navigate = useNavigate();
    const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

    return (
        <AppHeader>
            <div className="flex items-center">
                <Logo
                    title={conversationTitle ?? "OpenFIng Assistant"}
                    description="Conversación activa"
                    onClick={() => void navigate("/")}
                />
            </div>

            <div className="flex items-center gap-2">
                <ProfileDialog />
                <ThemeToggle />
                {/* <SettingsDialog /> */}
                {isAuthenticated && <SidebarTrigger />}
            </div>
        </AppHeader>
    );
};
