import { useState } from "react";

interface useCopyToClipboard {
    content: string;
    onCopy?: () => void;
}

export const useCopyToClipboard = ({ content, onCopy }: useCopyToClipboard) => {
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
        await navigator.clipboard.writeText(content);
        setCopied(true);
        onCopy?.();
        setTimeout(() => setCopied(false), 2000);
    };

    return { copied, handleCopy };
};
