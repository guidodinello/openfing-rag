import { ReactNode, createContext, useMemo, useState } from "react";

interface IConfig {
    isOpen: boolean;
}

interface IConfigContext {
    config: IConfig;
    toggleSidebar: () => void;
    setConfiguration: (configuration: Partial) => void;
}

const INITIAL_CONFIG: IConfig = {
    isOpen: true,
};

const INITIAL_CONFIG_CONTEXT: IConfigContext = {
    config: INITIAL_CONFIG,
    toggleSidebar: () => {},
    setConfiguration: () => {},
};

export const ConfigContext = createContext(INITIAL_CONFIG_CONTEXT);

export const ConfigProvider = ({ children }: { children: ReactNode }) => {
    
    const [config, setConfig] = useState(INITIAL_CONFIG);

    const toggleSidebar = () => {
    
        setConfig((prev) => ({ ...prev, isOpen: !prev.isOpen }));
    };

    const setConfiguration = (configuration: Partial) => {
        setConfig((prev) => ({ ...prev, ...configuration }));
    };
    const value = useMemo(() => ({
        config,    
        toggleSidebar,
        setConfiguration,
    }), [config]);

    return (
        <ConfigContext.Provider value={value}>
        {children}
        </ConfigContext.Provider>
    );
};