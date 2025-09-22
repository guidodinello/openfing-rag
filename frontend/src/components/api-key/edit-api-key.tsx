import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { LuCheck, LuX } from "react-icons/lu";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form";
import { apiKeySchema, type ApiKeyForm } from "./types";
import { useApiKeyStore } from "@/stores/api-key-store";

interface ApiKeyFormProps {
    onSubmit: (data: ApiKeyForm) => void;
    onCancel: () => void;
}

export const EditApiKey = ({ onSubmit, onCancel }: ApiKeyFormProps) => {
    const apiKey = useApiKeyStore((state) => state.apiKey);

    const form = useForm<ApiKeyForm>({
        resolver: zodResolver(apiKeySchema),
        defaultValues: { apiKey: apiKey ?? "" },
        mode: "onChange",
    });

    return (
        <Form {...form}>
            <form
                onSubmit={(e) => void form.handleSubmit(onSubmit)(e)}
                className="space-y-3"
            >
                <FormField
                    control={form.control}
                    name="apiKey"
                    render={({ field }) => (
                        <FormItem>
                            <FormLabel htmlFor="apiKey" className="sr-only">
                                API Key
                            </FormLabel>
                            <FormControl>
                                <Input
                                    {...field}
                                    id="apiKey"
                                    placeholder="sk-..."
                                    className="text-xs font-mono"
                                />
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )}
                />

                <div className="flex gap-2">
                    <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={onCancel}
                        className="flex-1"
                    >
                        <LuX className="size-3 mr-1" />
                        Cancelar
                    </Button>
                    <Button
                        type="submit"
                        size="sm"
                        disabled={!form.formState.isValid}
                        className="flex-1"
                    >
                        <LuCheck className="size-3 mr-1" />
                        Guardar
                    </Button>
                </div>
            </form>
        </Form>
    );
};
