import { Icon } from "@/components/icons";
import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuTrigger,
    DropdownMenuSeparator,
    DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import { ApiKeySection } from "./api-key/api-key-sections";

export const SettingsDialog = () => {
    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon">
                    <Icon.Settings className="size-4" />
                    <span className="sr-only">Configuración</span>
                </Button>
            </DropdownMenuTrigger>

            <DropdownMenuContent align="end" className="w-80">
                <DropdownMenuLabel className="flex items-center gap-2">
                    <Icon.Key className="size-4" />
                    Configuración
                </DropdownMenuLabel>

                <DropdownMenuSeparator />

                {/* TODO: use proper ui components instead of divs, ther a DropdownMenuItem and stuff */}
                <div className="p-3 space-y-4">
                    <ApiKeySection />

                    <div className="pt-2 border-t">
                        <p className="text-xs text-muted-foreground">
                            Tu API key se almacena localmente y nunca se
                            comparte.
                        </p>
                    </div>
                </div>
            </DropdownMenuContent>
        </DropdownMenu>
    );
};
