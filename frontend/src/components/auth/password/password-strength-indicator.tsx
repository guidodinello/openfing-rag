import { cn } from "@/lib/utils";

const STRENGTH_COLORS = [
    "bg-red-500",
    "bg-red-400",
    "bg-yellow-500",
    "bg-green-400",
    "bg-green-500",
] as const;

const STRENGTH_LABELS = [
    "Very Weak",
    "Weak",
    "Fair",
    "Good",
    "Strong",
] as const;

interface PasswordStrengthIndicatorProps {
    password: string;
    strength: number;
    className?: string;
}

export const PasswordStrengthIndicator = ({
    password,
    strength,
    className,
}: PasswordStrengthIndicatorProps) => {
    if (!password) return null;

    return (
        <div className={cn("space-y-2", className)}>
            <div className="flex space-x-1">
                {[1, 2, 3, 4, 5].map((level) => (
                    <div
                        key={level}
                        className={cn(
                            "h-1 w-1/5 rounded",
                            level <= strength
                                ? STRENGTH_COLORS[strength - 1]
                                : "bg-gray-200",
                        )}
                    />
                ))}
            </div>
            <p className="text-xs text-muted-foreground">
                Password strength: {STRENGTH_LABELS[strength - 1] || "Too weak"}
            </p>
        </div>
    );
};
