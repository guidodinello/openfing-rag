import { Button } from "@/components/ui/button";
import { Icon, type IconComponent } from "@/components/icons";
import { Input } from "@/components/ui/input";
import type { Transcription } from "@/types/transcription";
import { useCopyToClipboard } from "@/hooks/use-copy-to-clipboard";
import { toast } from "sonner";
import { AppHeader } from "../app-header";
import { Logo } from "../logo";
import { ProfileDialog } from "../profile-dialog";
import { ThemeToggle } from "../theme-toggle";
import { SidebarTrigger, useSidebar } from "../ui/sidebar";
import { useAuthStore } from "@/stores/auth-store";

interface TranscriptionHeaderProps {
    readonly transcription: Transcription;
    readonly searchQuery: string;
    readonly onSearchChange: (query: string) => void;
    readonly showSidebar: boolean;
    readonly onToggleSidebar: () => void;
}

const downloadFile = (content: string, title: string) => {
    const url = URL.createObjectURL(
        new Blob([content], { type: "text/plain" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = title;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
};

const downloadTranscription = (transcription: Transcription) =>
    downloadFile(
        transcription.content,
        `course-${transcription.course_id}_lesson-${transcription.lesson_id}-${transcription.lesson_title}.txt`,
    );

export const TranscriptionHeader = ({
    transcription,
    searchQuery,
    onSearchChange,
}: TranscriptionHeaderProps) => {
    const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

    const { handleCopy: copyUrl } = useCopyToClipboard({
        content: window.location.href,
        onCopy: () => toast.success("URL copied to clipboard!"),
    });

    return (
        <AppHeader>
            <div className="flex items-center gap-2">
                <Logo
                    title={`${transcription.course_id} - Clase ${transcription.lesson_title}`}
                    description={`Transcripción • ${transcription.transcriber.identifier} ${transcription.transcriber.size}`}
                />
            </div>

            <div className="flex items-center gap-2 flex-1 max-w-md">
                <SearchBar value={searchQuery} onChange={onSearchChange} />
            </div>

            <div className="flex items-center gap-12">
                <div className="flex items-center gap-2">
                    <HeaderItem
                        action={() => downloadTranscription(transcription)}
                        icon={Icon.Download}
                    />
                    <HeaderItem action={copyUrl} icon={Icon.Share} />
                </div>

                <div className="flex items-center gap-2">
                    <ProfileDialog />
                    <ThemeToggle />
                    {isAuthenticated && <SidebarTrigger />}
                </div>
            </div>
        </AppHeader>
    );
};

const HeaderItem = ({
    action,
    icon: Icon,
}: {
    action: () => void;
    icon: IconComponent;
}) => {
    return (
        <Button variant="ghost" size="icon" onClick={action}>
            <Icon className="size-4" />
        </Button>
    );
};

const SearchBar = ({
    value,
    onChange,
}: {
    value: string;
    onChange: (value: string) => void;
}) => (
    <div className="relative flex-1">
        <Icon.Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
        <Input
            type="search"
            placeholder="Buscar en transcripción..."
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="pl-9"
        />
    </div>
);
