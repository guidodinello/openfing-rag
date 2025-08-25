import type { ReactNode } from "react";

interface AppHeaderProps {
    readonly children: ReactNode;
}

export const AppHeader = ({ children }: AppHeaderProps) => {
    return (
        <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
            <div className="flex items-center justify-between px-4 py-3">
                {children}
            </div>
        </header>
    );
};
