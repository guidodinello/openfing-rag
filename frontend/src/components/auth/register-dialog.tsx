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
import { useRegister } from "@/hooks/use-auth";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import {
    registerCredentialsSchema,
    type RegisterCredentials,
} from "@/types/auth";
import { getPasswordStrength } from "@/utils/passwords";
import { PasswordInput } from "./password/password-input";
import { PasswordStrengthIndicator } from "./password/password-strength-indicator";
import { FormMutationErrors } from "../form-errors";

interface RegisterDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSwitchToLogin: () => void;
}

export const RegisterDialog = ({
    open,
    onOpenChange,
    onSwitchToLogin,
}: RegisterDialogProps) => {
    const registerMutation = useRegister();

    const form = useForm<RegisterCredentials>({
        resolver: zodResolver(registerCredentialsSchema),
        defaultValues: {
            email: "",
            username: "",
            password: "",
            confirmPassword: "",
        },
    });

    const password = form.watch("password");
    const passwordStrength = getPasswordStrength(password || "");

    const onSubmit = (data: RegisterCredentials) => {
        registerMutation.mutate(data, {
            onSuccess: () => {
                form.reset();
                onOpenChange(false);
            },
        });
    };

    const isLoading = registerMutation.isPending || form.formState.isSubmitting;

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-md max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>Create your account</DialogTitle>
                    <DialogDescription>
                        Join us to access your conversation history and
                        personalized experience.
                    </DialogDescription>
                </DialogHeader>

                <Form {...form}>
                    <form
                        onSubmit={form.handleSubmit(onSubmit)}
                        className="space-y-4"
                    >
                        <FormField
                            control={form.control}
                            name="email"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Email</FormLabel>
                                    <FormControl>
                                        <Input
                                            type="email"
                                            placeholder="your.email@example.com"
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
                                            placeholder="Create a strong password"
                                            disabled={isLoading}
                                            {...field}
                                        />
                                    </FormControl>
                                    <PasswordStrengthIndicator
                                        password={password || ""}
                                        strength={passwordStrength}
                                    />
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        <FormField
                            control={form.control}
                            name="confirmPassword"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Confirm Password</FormLabel>
                                    <FormControl>
                                        <PasswordInput
                                            placeholder="Confirm your password"
                                            disabled={isLoading}
                                            {...field}
                                        />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        <FormMutationErrors mutation={registerMutation} />

                        <div className="flex flex-col gap-2">
                            <Button
                                type="submit"
                                disabled={isLoading}
                                className="w-full"
                            >
                                {isLoading ? (
                                    <>
                                        <LuLoader className="size-4 mr-2 animate-spin" />
                                        Creating account...
                                    </>
                                ) : (
                                    "Create account"
                                )}
                            </Button>

                            <div className="text-center">
                                <span className="text-sm text-muted-foreground">
                                    Already have an account?{" "}
                                    <Button
                                        type="button"
                                        variant="link"
                                        className="p-0 h-auto font-semibold"
                                        onClick={onSwitchToLogin}
                                        disabled={isLoading}
                                    >
                                        Sign in
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
