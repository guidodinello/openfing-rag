import { useState } from "react";
import { LuEye, LuEyeOff, LuLoader } from "react-icons/lu";
import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useLogin } from "@/hooks/use-auth";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { loginCredentialsSchema, type LoginCredentials } from "@/types/auth";

interface LoginDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export const LoginDialog = ({ open, onOpenChange }: LoginDialogProps) => {
    const [showPassword, setShowPassword] = useState(false);
    const loginMutation = useLogin();

    const {
        register,
        handleSubmit,
        formState: { errors, isSubmitting },
        reset,
    } = useForm<LoginCredentials>({
        resolver: zodResolver(loginCredentialsSchema),
        defaultValues: {
            username: "",
            password: "",
        },
    });

    const onSubmit = async (data: LoginCredentials) => {
        loginMutation.mutate(data, {
            onSuccess: () => {
                reset();
                onOpenChange(false);
            },
        });
    };

    const isLoading = loginMutation.isPending || isSubmitting;

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

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="username">Username</Label>
                        <Input
                            id="username"
                            type="text"
                            placeholder="your-username"
                            {...register("username")}
                            disabled={isLoading}
                            className={errors.username ? "border-red-500" : ""}
                        />
                        {errors.username && (
                            <p className="text-sm text-red-500">
                                {errors.username.message}
                            </p>
                        )}
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="password">Password</Label>
                        <div className="relative">
                            <Input
                                id="password"
                                type={showPassword ? "text" : "password"}
                                placeholder="Enter your password"
                                {...register("password")}
                                disabled={isLoading}
                                className={`pr-10 ${errors.password ? "border-red-500" : ""}`}
                            />
                            <Button
                                type="button"
                                variant="ghost"
                                size="icon"
                                className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                                onClick={() => setShowPassword(!showPassword)}
                                disabled={loginMutation.isPending}
                            >
                                {showPassword ? (
                                    <LuEyeOff className="size-4" />
                                ) : (
                                    <LuEye className="size-4" />
                                )}
                            </Button>
                        </div>
                    </div>

                    {loginMutation.error && (
                        <div className="text-sm text-red-500 text-center">
                            {loginMutation.error.message ||
                                "Login failed. Please try again."}
                        </div>
                    )}

                    <div className="flex flex-col gap-2">
                        <Button
                            type="submit"
                            disabled={loginMutation.isPending}
                            className="w-full"
                        >
                            {loginMutation.isPending ? (
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
                                    onClick={() => {
                                        // Implement registration flow
                                        console.log("Not implemented yet");
                                    }}
                                >
                                    Sign up
                                </Button>
                            </span>
                        </div>
                    </div>
                </form>

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
                    disabled={loginMutation.isPending}
                    className="w-full"
                >
                    Continue without account
                </Button>
            </DialogContent>
        </Dialog>
    );
};
