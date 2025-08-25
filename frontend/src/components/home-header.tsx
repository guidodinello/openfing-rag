import { SidebarTrigger } from "./ui/sidebar";
import { Logo } from "./logo";
import { useAuthStore } from "@/stores/auth-store";
import { AppHeader } from "./app-header";
import { SettingsDialog } from "./settings-dialog";
import { ThemeToggle } from "./theme-toggle";
import { ProfileDialog } from "./profile-dialog";

export const HomeHeader = () => {
    const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

    return (
        <AppHeader>
            <div className="flex items-center gap-3">
                <Logo
                    title="OpenFIng Assistant"
                    description="Asistente inteligente para clases de OpenFIng"
                />
            </div>

            <div className="flex items-center gap-2">
                <ProfileDialog />
                <ThemeToggle />
                <SettingsDialog />
                {isAuthenticated && <SidebarTrigger />}
            </div>
        </AppHeader>
    );
};
