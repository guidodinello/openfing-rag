import type { ReactNode } from "react";
import { AppSidebar } from "./app-sidebar";
import { SidebarInset } from "./ui/sidebar";
import { HomeHeader } from "./home-header";
import { useLocation } from "react-router";
import { useAuthStore } from "@/stores/auth-store";

interface LayoutProps {
    children: ReactNode;
}

export const Layout = ({ children }: LayoutProps) => {
    const location = useLocation();
    const isHomePage = location.pathname === "/";
    const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

    return (
        <>
            <SidebarInset>
                <div className="min-h-screen bg-background w-full">
                    {isHomePage && <HomeHeader />}
                    {children}
                </div>
            </SidebarInset>
            {isAuthenticated && <AppSidebar />}
        </>
    );
};
