import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarGroup,
    SidebarGroupContent,
    SidebarGroupLabel,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
    SidebarMenuSkeleton,
    useSidebar,
} from "@/components/ui/sidebar";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import {
    useConversationsQuery,
    useDeleteConversationMutation,
} from "@/hooks/use-conversation";
import type { Conversation } from "@/types/conversation";
import { useNavigate } from "react-router";
import { useState } from "react";
import { RenameConversationDialog } from "./rename-conversation-dialog";
import { formatDate } from "@/utils/dates";
import { Icon } from "./icons";

interface RenameDialogState {
    open: boolean;
    conversation: Conversation | null;
}

export const AppSidebar = () => {
    const { data: conversations = [], isLoading } = useConversationsQuery();
    const deleteConversation = useDeleteConversationMutation();
    const navigate = useNavigate();
    const [renameDialog, setRenameDialog] = useState<RenameDialogState>({
        open: false,
        conversation: null,
    });
    const { setOpenMobile } = useSidebar();

    const handleNewChat = () => void navigate("/conversation/new");

    const handleSelectConversation = (conversationId: Conversation["id"]) => {
        void navigate(`/conversation/${conversationId}`);
        setOpenMobile(false);
    };

    const handleDeleteConversation = (conversationId: Conversation["id"]) =>
        deleteConversation.mutate(conversationId);

    const handleRenameConversation = (conversation: Conversation) =>
        setRenameDialog({ open: true, conversation });
    const handleCloseRenameDialog = () =>
        setRenameDialog({ open: false, conversation: null });

    return (
        <>
            <Sidebar side="right" collapsible="offcanvas" className="border-l">
                <SidebarHeader className="border-b p-4">
                    <Button
                        onClick={handleNewChat}
                        className="w-full justify-start gap-2"
                        variant="outline"
                    >
                        <Icon.Plus className="size-4" />
                        Nueva conversación
                    </Button>
                </SidebarHeader>

                <SidebarContent>
                    <SidebarGroup className="gap-4">
                        <SidebarGroupLabel>
                            Conversaciones recientes
                        </SidebarGroupLabel>
                        <SidebarGroupContent>
                            <SidebarMenu>
                                {isLoading
                                    ? Array.from({ length: 5 }).map(
                                          (_, index) => (
                                              <SidebarMenuItem
                                                  key={index}
                                                  className="p-2"
                                              >
                                                  <SidebarMenuSkeleton
                                                      showIcon
                                                  />
                                              </SidebarMenuItem>
                                          ),
                                      )
                                    : conversations.map((c) => (
                                          <ConversationSidebarItem
                                              key={c.id}
                                              conversation={c}
                                              onSelect={
                                                  handleSelectConversation
                                              }
                                              onDelete={
                                                  handleDeleteConversation
                                              }
                                              onRename={
                                                  handleRenameConversation
                                              }
                                          />
                                      ))}
                            </SidebarMenu>
                        </SidebarGroupContent>
                    </SidebarGroup>
                </SidebarContent>

                <SidebarFooter className="border-t p-4"></SidebarFooter>
            </Sidebar>

            <RenameConversationDialog
                conversation={renameDialog.conversation}
                open={renameDialog.open}
                onOpenChange={handleCloseRenameDialog}
            />
        </>
    );
};

interface SidebarConversationItemProps {
    conversation: Conversation;
    onSelect: (id: Conversation["id"]) => void;
    onDelete: (id: Conversation["id"]) => void;
    onRename: (conversation: Conversation) => void;
}
const ConversationSidebarItem = ({
    conversation,
    onSelect,
    onDelete,
    onRename,
}: SidebarConversationItemProps) => {
    return (
        <SidebarMenuItem className="min-h-7">
            <div className="flex items-center justify-between gap-2 w-full">
                <SidebarMenuButton
                    onClick={() => onSelect(conversation.id)}
                    className="flex-1 justify-start h-auto py-1"
                >
                    <Icon.MessageSquare className="size-4 shrink-0" />
                    <div className="flex-1 min-w-0">
                        <div className="truncate font-medium">
                            {conversation.title}
                        </div>
                        <div className="text-xs text-muted-foreground">
                            {formatDate(conversation.updated_at)}
                        </div>
                    </div>
                </SidebarMenuButton>

                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button
                            variant="ghost"
                            className="w-8 h-full shrink-0 justify-center"
                        >
                            <Icon.Ellipsis className="size-4" />
                            <span className="sr-only">
                                Opciones de conversación
                            </span>
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="start" side="right">
                        <DropdownMenuItem
                            onClick={() => onRename(conversation)}
                        >
                            <Icon.Pencil className="size-4 mr-1" />
                            Renombrar
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                            onClick={() => onDelete(conversation.id)}
                            className="text-red-600 focus:text-red-600"
                        >
                            <Icon.Trash className="size-4 mr-1" />
                            Eliminar
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            </div>
        </SidebarMenuItem>
    );
};
