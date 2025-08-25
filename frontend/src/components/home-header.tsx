import { ThemeToggle } from "./theme-toggle";
import { SettingsDialog } from "@/components/settings-dialog";
import { ProfileDialog } from "./profile-dialog";
import { SidebarTrigger } from "./ui/sidebar";
import { useAuthStore } from "@/stores/auth-store";
import { Logo } from "./logo";

export const HomeHeader = () => {
    const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

    return (
        <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
            <div className="flex items-center justify-between px-4 py-3">
                <Logo
                    title="OpenFIng Assistant"
                    description="Asistente inteligente para clases de OpenFIng"
                />

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
