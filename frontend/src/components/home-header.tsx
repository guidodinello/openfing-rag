import { ThemeToggle } from "./theme-toggle";
import { SettingsDialog } from "@/components/settings-dialog";
import { ProfileDialog } from "./profile-dialog";
import { SidebarTrigger } from "./ui/sidebar";
import { LuGraduationCap } from "react-icons/lu";
import { useAuthStore } from "@/stores/auth-store";

export const HomeHeader = () => {
    const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

    return (
        <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
            <div className="flex items-center justify-between px-4 py-3">
                <div className="flex items-center gap-2">
                    <div className="flex items-center justify-center size-8 bg-blue-600 rounded-lg">
                        <LuGraduationCap className="size-5 text-white" />
                    </div>
                    <div>
                        <h1 className="text-lg font-semibold">
                            OpenFIng Assistant
                        </h1>
                        <p className="text-xs text-muted-foreground">
                            Asistente inteligente para clases de OpenFIng
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    {isAuthenticated && <SidebarTrigger />}
                    <ProfileDialog />
                    <ThemeToggle />
                    <SettingsDialog />
                </div>
            </div>
        </header>
    );
};
