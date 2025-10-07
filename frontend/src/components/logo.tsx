import { cn } from "@/lib/utils";
import { Icon } from "@/components/icons";

interface LogoProps {
    title: string;
    description: string;
    onClick?: () => void;
}

export const Logo = ({ title, description, onClick }: LogoProps) => {
    return (
        <div className="flex items-center gap-2">
            <div className="flex items-center justify-center size-8 bg-blue-600 rounded-lg shrink-0">
                <Icon.GraduationCap
                    className={cn(
                        "size-5 text-white",
                        onClick && "cursor-pointer",
                    )}
                    onClick={onClick}
                />
            </div>
            <div>
                <h1 className="md:text-lg font-semibold">{title}</h1>
                <p className="text-xs text-muted-foreground hidden md:block">
                    {description}
                </p>
            </div>
        </div>
    );
};
