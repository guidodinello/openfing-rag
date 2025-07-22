import { useState } from "react";

export const useCopyToClipboard = (content: string) => {
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
        await navigator.clipboard.writeText(content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return { copied, handleCopy };
};
