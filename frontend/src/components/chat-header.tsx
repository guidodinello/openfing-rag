import { LuMessageSquare, LuArrowLeft } from "react-icons/lu";
import { useNavigate } from "react-router";
import { Button } from "@/components/ui/button";
import { Logo } from "./logo";
import { AppHeader } from "./app-header";
import { SettingsDialog } from "./settings-dialog";
import { ThemeToggle } from "./theme-toggle";
import { ProfileDialog } from "./profile-dialog";

interface ChatHeaderProps {
    readonly conversationTitle?: string;
    readonly showMessageButton?: boolean;
    readonly onMessageClick?: () => void;
}

export const ChatHeader = ({
    conversationTitle,
    showMessageButton = false,
    onMessageClick,
}: ChatHeaderProps) => {
    const navigate = useNavigate();

    const handleBackToHome = () => navigate("/");

    return (
        <AppHeader>
            <div className="flex items-center gap-3">
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={handleBackToHome}
                    className="shrink-0"
                >
                    <LuArrowLeft className="size-4" />
                    <span className="sr-only">Volver al inicio</span>
                </Button>

                <Logo
                    title={conversationTitle || "OpenFIng Assistant"}
                    description="Conversación activa"
                />
            </div>

            <div className="flex items-center gap-2">
                <ProfileDialog />
                <ThemeToggle />
                <SettingsDialog />
                {showMessageButton && (
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={onMessageClick}
                    >
                        <LuMessageSquare className="size-4" />
                        <span className="sr-only">Mensajes</span>
                    </Button>
                )}
            </div>
        </AppHeader>
    );
};
