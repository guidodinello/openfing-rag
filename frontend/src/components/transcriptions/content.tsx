import type { Transcription } from "@/types/transcription";
import { useMemo } from "react";

interface TranscriptionContentProps {
    readonly content: Transcription["content"];
    readonly paragraphSpacing?: "tight" | "normal" | "loose";
}

export const TranscriptionContent = ({
    content,
    paragraphSpacing = "normal",
}: TranscriptionContentProps) => {
    const spacingClasses = {
        tight: "mb-2",
        normal: "mb-4",
        loose: "mb-6",
    };

    const formattedContent = useMemo(() => {
        const sentences = content.split(/([.!?]\s+)/);
        let result = "";
        let currentParagraph = "";
        let sentenceCount = 0;

        for (let i = 0; i < sentences.length; i += 2) {
            const sentence = (sentences[i] || "") + (sentences[i + 1] || "");
            currentParagraph += sentence;
            sentenceCount++;

            if (sentenceCount >= 3) {
                result += `<p class="${spacingClasses[paragraphSpacing]}">${currentParagraph.trim()}</p>`;
                currentParagraph = "";
                sentenceCount = 0;
            }
        }

        if (currentParagraph.trim()) {
            result += `<p class="${spacingClasses[paragraphSpacing]}">${currentParagraph.trim()}</p>`;
        }

        return result;
    }, [content, paragraphSpacing]);

    return (
        <div className="flex-1 min-h-0 overflow-y-auto">
            <div className="max-w-[120ch] mx-auto px-6 py-12">
                <article>
                    <div
                        className="text-base md:text-lg leading-relaxed text-foreground/90"
                        dangerouslySetInnerHTML={{
                            __html: formattedContent,
                        }}
                    />
                </article>
            </div>
        </div>
    );
};
