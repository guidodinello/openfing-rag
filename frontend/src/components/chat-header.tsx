import { LuGraduationCap, LuMessageSquare, LuArrowLeft } from "react-icons/lu";
import { useNavigate } from "react-router";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "./theme-toggle";
import { SettingsDialog } from "@/components/settings-dialog";
import { ProfileDialog } from "./profile-dialog";

interface ChatHeaderProps {
    readonly conversationTitle?: string;
}

export const ChatHeader = ({ conversationTitle }: ChatHeaderProps) => {
    const navigate = useNavigate();

    const handleBackToHome = () => navigate("/");

    return (
        <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
            <div className="flex items-center justify-between px-4 py-3">
                <div className="flex items-center gap-3">
                    {/* Botón para volver al home */}
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={handleBackToHome}
                        className="shrink-0"
                    >
                        <LuArrowLeft className="size-4" />
                        <span className="sr-only">Volver al inicio</span>
                    </Button>

                    <div className="flex items-center gap-2">
                        <div className="flex items-center justify-center size-8 bg-blue-600 rounded-lg">
                            <LuGraduationCap className="size-5 text-white" />
                        </div>
                        <div>
                            <h1 className="text-lg font-semibold">
                                {conversationTitle || "OpenFIng Assistant"}
                            </h1>
                            <p className="text-xs text-muted-foreground">
                                Conversación activa
                            </p>
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <ThemeToggle />
                    <SettingsDialog />
                    <ProfileDialog />

                    <Button variant="ghost" size="icon">
                        <LuMessageSquare className="size-4" />
                    </Button>
                </div>
            </div>
        </header>
    );
};
