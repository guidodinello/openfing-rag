import { Icon } from "@/components/icons";
import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuTrigger,
    DropdownMenuSeparator,
    DropdownMenuLabel,
    DropdownMenuGroup,
    DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
import { useLogout } from "@/hooks/use-auth";
import { useState } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { useUserProfileQuery } from "@/hooks/use-user";
import { AuthDialogManager } from "./auth/auth-dialog";
import {
    Tooltip,
    TooltipContent,
    TooltipTrigger,
} from "@/components/ui/tooltip";

export const ProfileDialog = () => {
    const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
    const { data: user, isLoading, error } = useUserProfileQuery();
    const logoutMutation = useLogout();
    const [showAuthDialog, setShowAuthDialog] = useState(false);

    const handleLogout = () => logoutMutation.mutate();

    if (!isAuthenticated) {
        return (
            <>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setShowAuthDialog(true)}
                        >
                            <Icon.LogIn className="size-4" />
                            <span className="sr-only">Login</span>
                        </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                        <p>Login</p>
                    </TooltipContent>
                </Tooltip>

                <AuthDialogManager
                    open={showAuthDialog}
                    onOpenChange={setShowAuthDialog}
                    initialMode="login"
                />
            </>
        );
    }

    if (isLoading) {
        return (
            <Button variant="ghost" size="icon" disabled>
                <Icon.Loader className="size-4 animate-spin" />
                <span className="sr-only">Loading profile</span>
            </Button>
        );
    }

    if (error) {
        return (
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <Button
                        variant="ghost"
                        size="icon"
                        className="text-red-500"
                    >
                        <Icon.User className="size-4" />
                        <span className="sr-only">Profile (Error)</span>
                    </Button>
                </DropdownMenuTrigger>

                <DropdownMenuContent align="end" className="w-80">
                    <DropdownMenuLabel className="text-red-500">
                        Error loading profile
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                        onClick={handleLogout}
                        disabled={logoutMutation.isPending}
                    >
                        <Icon.LogOut className="size-4 mr-2" />
                        {logoutMutation.isPending ? "Logging out..." : "Logout"}
                    </DropdownMenuItem>
                </DropdownMenuContent>
            </DropdownMenu>
        );
    }

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon">
                    <Icon.User className="size-4" />
                    <span className="sr-only">Profile</span>
                </Button>
            </DropdownMenuTrigger>

            <DropdownMenuContent align="end" className="w-80">
                <DropdownMenuLabel className="flex items-center gap-2">
                    <Icon.User className="size-4" />
                    Profile
                </DropdownMenuLabel>

                <DropdownMenuSeparator />

                <DropdownMenuGroup className="p-3 space-y-2">
                    <div className="flex flex-col space-y-1">
                        <p className="text-sm font-medium">{user?.email}</p>
                        <p className="text-xs text-muted-foreground">
                            {user?.username}
                        </p>
                    </div>
                </DropdownMenuGroup>

                <DropdownMenuSeparator />

                <DropdownMenuItem
                    onClick={handleLogout}
                    disabled={logoutMutation.isPending}
                >
                    <Icon.LogOut className="size-4 mr-2" />
                    {logoutMutation.isPending ? "Logging out..." : "Logout"}
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    );
};
