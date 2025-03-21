import { ReactNode, createContext, useMemo, useState } from "react";

interface IConfig {
    lastConversation: string[];
    model: string;
    course: string; 
    class: number;
}

interface IConfigContext {
    config: IConfig;
    setConfiguration: (configuration: IConfig) => void;
}
const INITIAL_CONFIG: IConfig = {
    lastConversation: [],
    model: "gpt-4o",
    course: "",
    class: 0,
};

const INITIAL_CONFIG_CONTEXT: IConfigContext = {
    config: INITIAL_CONFIG,
    setConfiguration: () => {},
};

export const ConfigContext = createContext<IConfigContext>(INITIAL_CONFIG_CONTEXT);

export const ConfigProvider = ({ children }: { children: ReactNode }) => {
    const [config, setConfig] = useState<IConfig>(INITIAL_CONFIG);

    const setConfiguration = (configuration: IConfig) => {
        setConfig((c) => ({ ...c, ...configuration }));
    };

    const value: IConfigContext = useMemo(
        () => ({ config, setConfiguration }),
        [config],
    );

    return (
        <ConfigContext.Provider value={value}>
            {children}
        </ConfigContext.Provider>
    );
};
