import { Icon } from "@/components/icons";
import { Badge } from "@/components/ui/badge";
import {
    Tooltip,
    TooltipContent,
    TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { cosineDistanceToSimilarity, floatToPercentage } from "@/utils/numbers";
import { formatSecondsToTimeWithHours } from "@/utils/dates";
import type { Source, SourceTimestamp } from "@/types/message";
import { Link } from "react-router";

interface SourceCitationsProps {
    readonly sources: Source[];
}

export const SourceCitations = ({ sources }: SourceCitationsProps) => (
    <div className="space-y-2">
        <div className="flex items-center gap-1 text-xs font-medium text-muted-foreground">
            <Icon.BookOpen className="size-3" />
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

const generateVideoUrl = (url: string, timestamp: SourceTimestamp) => {
    // Format expected: https://open.fing.edu.uy/courses/2022/6/?t=626,627
    const start = Math.floor(timestamp.start);
    const end = Math.floor(timestamp.end);

    const timestampedUrl = new URL(url);
    timestampedUrl.searchParams.set("t", `${start},${end}`);
    return timestampedUrl.toString();
};

type ConfidenceLevel = "high" | "medium" | "low";

// Mirrors the original distance-based cutoffs (>20% distance = worst match, >15% = medium),
// converted to similarity (1 - distance): distance 20% -> similarity 80%, distance 15% -> similarity 85%.
const getConfidenceLevel = (similarity: number): ConfidenceLevel => {
    const percentage = floatToPercentage(similarity);
    if (percentage >= 85) return "high";
    if (percentage >= 80) return "medium";
    return "low";
};

const confidenceBadgeStyles: Record<ConfidenceLevel, string> = {
    high: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
    medium: "bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300",
    low: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
};

const SourceCard = ({ source }: SourceCardProps) => {
    // source.confidence is the raw cosine distance from pgvector (lower = more relevant).
    const similarity = cosineDistanceToSimilarity(source.confidence);
    const badgeStyle = confidenceBadgeStyles[getConfidenceLevel(similarity)];

    return (
        <a
            href={generateVideoUrl(source.url, source.timestamp)}
            target="_blank"
            rel="noopener noreferrer"
            className={cn(
                "block w-full p-3 text-left rounded-md border transition-all duration-200",
                "hover:bg-blue-50 dark:hover:bg-blue-950",
                "border-blue-200 dark:border-blue-800",
                "bg-transparent hover:border-blue-300 dark:hover:border-blue-700",
                "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2",
                "group/source",
            )}
        >
            <div className="flex items-center justify-between w-full">
                <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm truncate group-hover/source:text-blue-700 dark:group-hover/source:text-blue-300 transition-colors">
                        {source.title}
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                        <Icon.Clock className="size-3" />
                        <span>
                            {formatSecondsToTimeWithHours(
                                source.timestamp.start,
                            )}{" "}
                            -{" "}
                            {formatSecondsToTimeWithHours(source.timestamp.end)}
                        </span>
                    </div>
                </div>

                <div className="flex items-center gap-2 ml-2">
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <div className="flex items-center gap-1">
                                <Badge
                                    variant="secondary"
                                    className={badgeStyle}
                                >
                                    <Icon.TrendingUp className="size-3 mr-1" />
                                    {floatToPercentage(similarity)}%
                                </Badge>
                            </div>
                        </TooltipTrigger>
                        <TooltipContent
                            sideOffset={8}
                            side="top"
                            className="max-w-xs"
                        >
                            <p className="text-sm">
                                La{" "}
                                <Link
                                    to="https://en.wikipedia.org/wiki/Cosine_similarity"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="underline hover:text-foreground"
                                >
                                    puntuación de similitud
                                </Link>{" "}
                                esta basada en la distancia coseno entre
                                vectores. Por lo que valores más altos indican
                                mayor similitud.
                            </p>
                        </TooltipContent>
                    </Tooltip>
                    <Icon.ExternalLink className="size-4 text-muted-foreground group-hover/source:text-blue-600 dark:group-hover/source:text-blue-400 transition-colors" />
                </div>
            </div>
        </a>
    );
};
