import { ThemeProvider as NextThemesProvider } from "next-themes";

export const ThemeProvider = ({
    children,
    ...props
}: Readonly<React.ComponentProps<typeof NextThemesProvider>>) => {
    return <NextThemesProvider {...props}>{children}</NextThemesProvider>;
};
