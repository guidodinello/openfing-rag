import {
    LuBookOpen,
    LuClock,
    LuExternalLink,
    LuTrendingUp,
} from "react-icons/lu";
import { Badge } from "@/components/ui/badge";
import type { Source, Timestamp } from "@/types/chat";
import { cn } from "@/lib/utils";
import { formatSecondsToTime } from "@/utils/dates";
import { floatToPercentage } from "@/utils/numbers";

interface SourceCitationsProps {
    readonly sources: Source[];
}

export const SourceCitations = ({ sources }: SourceCitationsProps) => (
    <div className="space-y-2">
        {" "}
        <div className="flex items-center gap-1 text-xs font-medium text-muted-foreground">
            <LuBookOpen className="size-3" />
            Fuentes:
        </div>
        <div className="space-y-2">
            {sources.map((source) => (
                <SourceCard key={source.id} source={source} />
            ))}
        </div>
    </div>
);

interface SourceCardProps {
    readonly source: Source;
}

const generateVideoUrl = (url: string, timestamp: Timestamp) => {
    // Format expected: https://open.fing.edu.uy/courses/2022/6/?t=626,627
    const start = Math.floor(timestamp.start);
    const end = Math.floor(timestamp.end);

    const timestampedUrl = new URL(url);
    timestampedUrl.searchParams.set("t", `${start},${end}`);
    return timestampedUrl.toString();
};

const SourceCard = ({ source }: SourceCardProps) => (
    <a
        href={generateVideoUrl(source.url, source.timestamp)}
        target="_blank"
        rel="noopener noreferrer"
        className={cn(
            "block w-full p-3 text-left rounded-md border transition-all duration-200",
            "hover:bg-green-50 dark:hover:bg-green-950",
            "border-green-200 dark:border-green-800",
            "bg-transparent hover:border-green-300 dark:hover:border-green-700",
            "focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2",
            "group",
        )}
    >
        <div className="flex items-start justify-between w-full">
            <div className="flex-1 min-w-0">
                <div className="font-medium text-sm truncate group-hover:text-green-700 dark:group-hover:text-green-300 transition-colors">
                    {source.title}
                </div>
                <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                    <LuClock className="size-3" />
                    <span>
                        {formatSecondsToTime(source.timestamp.start)} -{" "}
                        {formatSecondsToTime(source.timestamp.end)}
                    </span>
                </div>
            </div>

            <div className="flex items-center gap-2 ml-2">
                <Badge
                    variant="secondary"
                    className="bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
                >
                    <LuTrendingUp className="size-3 mr-1" />
                    {floatToPercentage(source.confidence)}%
                </Badge>
                <LuExternalLink className="size-3 text-muted-foreground group-hover:text-green-600 dark:group-hover:text-green-400 transition-colors" />
            </div>
        </div>
    </a>
);
