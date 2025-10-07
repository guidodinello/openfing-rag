import { LuLoader } from "react-icons/lu";
import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form";
import { useLogin } from "@/hooks/use-auth";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { loginCredentialsSchema, type LoginCredentials } from "@/types/auth";
import { PasswordInput } from "./password/password-input";

interface LoginDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSwitchToRegister: () => void;
}

export const LoginDialog = ({
    open,
    onOpenChange,
    onSwitchToRegister,
}: LoginDialogProps) => {
    const loginMutation = useLogin();

    const form = useForm<LoginCredentials>({
        resolver: zodResolver(loginCredentialsSchema),
        defaultValues: {
            username: "",
            password: "",
        },
    });

    const onSubmit = (data: LoginCredentials) => {
        loginMutation.mutate(
            {
                credentials: data,
                rememberMe: true,
            },
            {
                onSuccess: () => {
                    form.reset();
                    onOpenChange(false);
                },
            },
        );
    };
    const isLoading = loginMutation.isPending || form.formState.isSubmitting;

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle>Sign in to your account</DialogTitle>
                    <DialogDescription>
                        Access your conversation history and personalized
                        experience.
                    </DialogDescription>
                </DialogHeader>

                <Form {...form}>
                    <form
                        onSubmit={form.handleSubmit(onSubmit)}
                        className="space-y-4"
                    >
                        <FormField
                            control={form.control}
                            name="username"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Username</FormLabel>
                                    <FormControl>
                                        <Input
                                            type="text"
                                            placeholder="your-username"
                                            disabled={isLoading}
                                            {...field}
                                        />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        <FormField
                            control={form.control}
                            name="password"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Password</FormLabel>
                                    <FormControl>
                                        <PasswordInput
                                            placeholder="Enter your password"
                                            disabled={isLoading}
                                            {...field}
                                        />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        <div className="flex flex-col gap-2">
                            <Button
                                type="submit"
                                disabled={isLoading}
                                className="w-full"
                            >
                                {isLoading ? (
                                    <>
                                        <LuLoader className="size-4 mr-2 animate-spin" />
                                        Signing in...
                                    </>
                                ) : (
                                    "Sign in"
                                )}
                            </Button>

                            <div className="text-center">
                                <span className="text-sm text-muted-foreground">
                                    Don't have an account?{" "}
                                    <Button
                                        type="button"
                                        variant="link"
                                        className="p-0 h-auto font-semibold"
                                        onClick={onSwitchToRegister}
                                        disabled={isLoading}
                                    >
                                        Sign up
                                    </Button>
                                </span>
                            </div>
                        </div>
                    </form>
                </Form>

                <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                        <span className="w-full border-t" />
                    </div>
                    <div className="relative flex justify-center text-xs uppercase">
                        <span className="bg-background px-2 text-muted-foreground">
                            Or continue as guest
                        </span>
                    </div>
                </div>

                <Button
                    variant="outline"
                    onClick={() => onOpenChange(false)}
                    disabled={isLoading}
                    className="w-full"
                >
                    Continue without account
                </Button>
            </DialogContent>
        </Dialog>
    );
};
