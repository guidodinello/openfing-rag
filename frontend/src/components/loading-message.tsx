import { LuBot } from "react-icons/lu";
import { Skeleton } from "@/components/ui/skeleton";

export const LoadingMessage = () => (
    <div className="flex gap-3">
        <div className="flex-shrink-0 size-8 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mt-1">
            <LuBot className="size-4 text-green-600 dark:text-green-400 animate-pulse" />
        </div>

        <div className="flex-1 max-w-[80%] md:max-w-[70%]">
            <div className="bg-muted rounded-2xl rounded-tl-md px-4 py-3">
                <div className="space-y-2">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-4/5" />
                    <Skeleton className="h-4 w-3/5" />
                </div>
            </div>

            <div className="mt-3 space-y-2">
                <div className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                    <div className="size-3 bg-muted rounded animate-pulse" />
                    Buscando fuentes...
                </div>
                <Skeleton className="h-12 w-full rounded-lg" />
                <Skeleton className="h-12 w-4/5 rounded-lg" />
            </div>
        </div>
    </div>
);
