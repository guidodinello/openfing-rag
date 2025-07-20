import { useState } from "react";
import { LuEye, LuEyeOff } from "react-icons/lu";
import { Button } from "@/components/ui/button";
import { maskApiKey } from "./types";

interface ApiKeyDisplayProps {
    apiKey: string;
    onEdit: () => void;
    onDelete: () => void;
}

export const ApiKeyDisplay = ({
    apiKey,
    onEdit,
    onDelete,
}: ApiKeyDisplayProps) => {
    const [isVisible, setIsVisible] = useState(false);

    return (
        <div className="space-y-2">
            <div className="flex items-center justify-between bg-muted rounded-lg p-3">
                <code className="text-xs font-mono flex-1 truncate">
                    {isVisible ? apiKey : maskApiKey(apiKey)}
                </code>

                <Button
                    variant="ghost"
                    size="icon"
                    className="size-6 shrink-0 ml-2"
                    onClick={() => setIsVisible(!isVisible)}
                    aria-label={isVisible ? "Ocultar" : "Mostrar"}
                >
                    {isVisible ? (
                        <LuEyeOff className="size-3" />
                    ) : (
                        <LuEye className="size-3" />
                    )}
                </Button>
            </div>

            <div className="flex gap-2">
                <Button
                    variant="outline"
                    size="sm"
                    onClick={onEdit}
                    className="flex-1"
                >
                    Editar
                </Button>
                <Button
                    variant="outline"
                    size="sm"
                    onClick={onDelete}
                    className="flex-1 text-destructive hover:text-destructive/90"
                >
                    Eliminar
                </Button>
            </div>
        </div>
    );
};
