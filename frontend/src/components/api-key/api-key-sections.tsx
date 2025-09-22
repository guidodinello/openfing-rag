import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useApiKeyStore } from "@/stores/api-key-store";
import type { ApiKeyForm } from "./types";
import { ApiKeyDisplay } from "./api-key-display";
import { EditApiKey } from "./edit-api-key";

export const ApiKeySection = () => {
    const apiKey = useApiKeyStore((state) => state.apiKey);
    const setApiKey = useApiKeyStore((state) => state.setApiKey);
    const clearApiKey = useApiKeyStore((state) => state.clearApiKey);
    const [isEditing, setIsEditing] = useState(false);

    const handleSave = (data: ApiKeyForm) => {
        setApiKey(data.apiKey);
        setIsEditing(false);
    };

    const handleDelete = () => {
        clearApiKey();
        setIsEditing(false);
    };

    const handleEdit = () => setIsEditing(true);
    const handleCancel = () => setIsEditing(false);

    return (
        <section className="space-y-3" aria-label="API Key Configuration">
            <div className="flex items-center justify-between">
                <span className="text-sm font-medium">API Key</span>
            </div>

            {isEditing ? (
                <EditApiKey onSubmit={handleSave} onCancel={handleCancel} />
            ) : apiKey ? (
                <ApiKeyDisplay
                    apiKey={apiKey}
                    onEdit={handleEdit}
                    onDelete={handleDelete}
                />
            ) : (
                <Button
                    variant="outline"
                    size="sm"
                    onClick={handleEdit}
                    className="w-full"
                    aria-label="Add API Key"
                >
                    Agregar API Key
                </Button>
            )}
        </section>
    );
};
