import {
    codeBlockLookBack,
    findCompleteCodeBlock,
    findPartialCodeBlock,
    loadHighlighter,
    useCodeBlockToHtml,
    allLangs,
    allLangsAlias,
    type CodeToHtmlOptions,
} from "@llm-ui/code";
import { markdownLookBack } from "@llm-ui/markdown";
import { useLLMOutput, type LLMOutputComponent } from "@llm-ui/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import parseHtml from "html-react-parser";
import { createHighlighterCore } from "shiki/core";
import { createOnigurumaEngine } from "shiki/engine/oniguruma";
import { bundledLanguagesInfo } from "shiki/langs";

import type { Message } from "@/types/message";
import { MESSAGE_ROLES } from "@/constants/message-roles";
import { cn } from "@/lib/utils";
import type { JSX } from "react/jsx-runtime";
import React from "react";

const highlighter = loadHighlighter(
    createHighlighterCore({
        langs: allLangs(bundledLanguagesInfo),
        langAlias: allLangsAlias(bundledLanguagesInfo),
        themes: [
            import("shiki/themes/github-dark.mjs"),
            import("shiki/themes/github-light.mjs"),
        ],
        engine: createOnigurumaEngine(() => import("shiki/wasm")),
    }),
);

const codeToHtmlOptions: CodeToHtmlOptions = {
    theme: "github-dark",
};

const createStyledComponent =
    <T extends keyof JSX.IntrinsicElements>(
        tag: T,
        baseStyles: string,
        userStyles?: string,
    ) =>
    (props: React.ComponentProps<T>) => {
        return React.createElement(
            tag,
            {
                ...props,
                className: cn(baseStyles, userStyles, props.className),
            },
            props.children,
        );
    };

const componentsBuilder = (variant: Message["role"]) => {
    const isUserMessage = variant === MESSAGE_ROLES.USER;
    const userTextStyle = isUserMessage ? "text-white" : "";

    return {
        h1: createStyledComponent(
            "h1",
            "text-lg font-semibold mb-2 mt-4 first:mt-0",
            userTextStyle,
        ),
        h2: createStyledComponent(
            "h2",
            "text-base font-semibold mb-2 mt-3 first:mt-0",
            userTextStyle,
        ),
        h3: createStyledComponent(
            "h3",
            "text-sm font-semibold mb-1 mt-3 first:mt-0",
            userTextStyle,
        ),
        p: createStyledComponent(
            "p",
            "text-sm leading-relaxed mb-2 last:mb-0",
            userTextStyle,
        ),
        ul: createStyledComponent(
            "ul",
            "list-disc pl-4 mb-2 space-y-1",
            userTextStyle,
        ),
        ol: createStyledComponent(
            "ol",
            "list-decimal pl-4 mb-2 space-y-1",
            userTextStyle,
        ),
        li: createStyledComponent("li", "text-sm", userTextStyle),
        strong: createStyledComponent("strong", "font-semibold", userTextStyle),
        em: createStyledComponent("em", "italic", userTextStyle),
        code: (props: React.ComponentProps<"code">) => {
            const isInline = !props.className?.includes("language-");
            if (isInline) {
                return (
                    <code
                        {...props}
                        className={cn(
                            "px-1 py-0.5 rounded text-sm font-mono",
                            isUserMessage
                                ? "bg-white/20 text-white"
                                : "bg-muted-foreground/20",
                            props.className,
                        )}
                    >
                        {props.children}
                    </code>
                );
            }
            return <code {...props} />;
        },
        blockquote: (props: React.ComponentProps<"blockquote">) => (
            <blockquote
                {...props}
                className={cn(
                    "border-l-4 pl-4 italic mb-2",
                    isUserMessage
                        ? "border-white/20 text-white/90"
                        : "border-muted-foreground/20",
                    props.className,
                )}
            >
                {props.children}
            </blockquote>
        ),
    };
};

const MarkdownComponent =
    (variant: Message["role"]): LLMOutputComponent =>
    ({ blockMatch }) => {
        const markdown = blockMatch.output;

        return (
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={componentsBuilder(variant)}
            >
                {markdown}
            </ReactMarkdown>
        );
    };

const CodeBlock: LLMOutputComponent = ({ blockMatch }) => {
    const { html, code } = useCodeBlockToHtml({
        markdownCodeBlock: blockMatch.output,
        highlighter,
        codeToHtmlOptions,
    });

    if (!html) {
        return (
            <pre className="bg-muted-foreground/10 rounded p-3 overflow-x-auto">
                <code className="text-sm font-mono">{code}</code>
            </pre>
        );
    }

    return (
        <div className="rounded overflow-hidden my-2">{parseHtml(html)}</div>
    );
};

interface RichTextProps {
    content: string;
    variant: Message["role"];
    className?: string;
}

export const RichText = ({
    content,
    variant,
    className = "",
}: Readonly<RichTextProps>) => {
    const { blockMatches } = useLLMOutput({
        llmOutput: content,
        fallbackBlock: {
            component: MarkdownComponent(variant),
            lookBack: markdownLookBack(),
        },
        blocks: [
            {
                component: CodeBlock,
                findCompleteMatch: findCompleteCodeBlock(),
                findPartialMatch: findPartialCodeBlock(),
                lookBack: codeBlockLookBack(),
            },
        ],
        isStreamFinished: true,
    });

    return (
        <div className={className}>
            {blockMatches.map((blockMatch, index) => {
                const Component = blockMatch.block.component;
                return <Component key={index} blockMatch={blockMatch} />;
            })}
        </div>
    );
};
