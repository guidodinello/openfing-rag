import { useState } from "react";
import { Icon } from "@/components/icons";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface PasswordInputProps
    extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> {
    ref?: React.Ref<HTMLInputElement>;
}

export const PasswordInput = ({
    placeholder = "Enter password",
    disabled = false,
    className,
    ref,
    ...inputProps
}: PasswordInputProps) => {
    const [showPassword, setShowPassword] = useState(false);

    return (
        <div className="relative">
            <Input
                ref={ref}
                type={showPassword ? "text" : "password"}
                placeholder={placeholder}
                disabled={disabled}
                className={cn("pr-10", className)}
                {...inputProps}
            />
            <Button
                type="button"
                variant="ghost"
                size="icon"
                className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                onClick={() => setShowPassword(!showPassword)}
                disabled={disabled}
                tabIndex={-1}
                aria-label={showPassword ? "Hide password" : "Show password"}
            >
                {showPassword ? (
                    <Icon.EyeOff className="size-4" />
                ) : (
                    <Icon.Eye className="size-4" />
                )}
            </Button>
        </div>
    );
};
