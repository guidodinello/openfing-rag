import { LuGraduationCap } from "react-icons/lu";

interface LogoProps {
    title: string;
    description: string;
}

export const Logo = ({ title, description }: LogoProps) => (
    <div className="flex items-center gap-2">
        <div className="flex items-center justify-center size-8 bg-blue-600 rounded-lg shrink-0">
            <LuGraduationCap className="size-5 text-white" />
        </div>
        <div>
            <h1 className="text-lg font-semibold">{title}</h1>
            <p className="text-xs text-muted-foreground hidden md:block">
                {description}
            </p>
        </div>
    </div>
);
