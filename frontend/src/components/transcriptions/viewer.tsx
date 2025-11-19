// TranscriptionViewer.tsx
import { useState, useMemo } from "react";
import { TranscriptionHeader } from "./header";
import { TranscriptionContent } from "./content";
import type { Transcription } from "@/types/transcription";

interface TranscriptionViewerProps {
    readonly transcription: Transcription;
}

// utils/search.ts
export const createAccentInsensitiveRegex = (searchTerm: string): RegExp => {
    if (!searchTerm) return /.^/; // Never matches

    // Escape special characters
    const escaped = searchTerm.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

    // Character mappings for Spanish
    const replacements: Array<[RegExp, string]> = [
        [/a/gi, "[aáàäâ]"],
        [/e/gi, "[eéèëê]"],
        [/i/gi, "[iíìïî]"],
        [/o/gi, "[oóòöô]"],
        [/u/gi, "[uúùüû]"],
        [/n/gi, "[nñ]"],
        [/c/gi, "[cç]"],
    ];

    let pattern = escaped;
    replacements.forEach(([regex, replacement]) => {
        pattern = pattern.replace(regex, replacement);
    });

    return new RegExp(`(${pattern})`, "gi");
};

export const TranscriptionViewer = ({
    transcription,
}: TranscriptionViewerProps) => {
    const [searchQuery, setSearchQuery] = useState("");
    const [showSidebar, setShowSidebar] = useState(true);

    const highlightedContent = useMemo(() => {
        if (!searchQuery.trim()) return transcription.content;

        try {
            const regex = createAccentInsensitiveRegex(searchQuery);
            return transcription.content.replace(
                regex,
                '<mark class="bg-yellow-300 dark:bg-yellow-600 rounded px-0.5">$1</mark>',
            );
        } catch (error) {
            console.warn("Search error:", error);
            return transcription.content;
        }
    }, [transcription.content, searchQuery]);

    return (
        <div className="flex flex-col h-screen">
            <TranscriptionHeader
                transcription={transcription}
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
                showSidebar={showSidebar}
                onToggleSidebar={() => setShowSidebar(!showSidebar)}
            />

            {/* min-h-0 is crucial here */}
            <div className="flex-1 min-h-0 flex overflow-hidden">
                <TranscriptionContent content={highlightedContent} />
            </div>
        </div>
    );
};
