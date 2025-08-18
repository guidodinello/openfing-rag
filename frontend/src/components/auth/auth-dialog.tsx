import { useState } from "react";
import { LoginDialog } from "./login-dialog";
import { RegisterDialog } from "./register-dialog";

type AuthModes = "login" | "register";

interface AuthDialogManagerProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    initialMode?: AuthModes;
}

export const AuthDialogManager = ({
    open,
    onOpenChange,
    initialMode = "login",
}: AuthDialogManagerProps) => {
    const [mode, setMode] = useState<AuthModes>(initialMode);

    return (
        <>
            <LoginDialog
                open={open && mode === "login"}
                onOpenChange={onOpenChange}
                onSwitchToRegister={() => setMode("register")}
            />
            <RegisterDialog
                open={open && mode === "register"}
                onOpenChange={onOpenChange}
                onSwitchToLogin={() => setMode("login")}
            />
        </>
    );
};
