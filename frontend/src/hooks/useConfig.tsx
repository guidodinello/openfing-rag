import { useContext } from "react";
import { ConfigContext } from "../contexts";

export const useConfig = () => {
    const context = useContext(ConfigContext);
    if (!context) throw new Error("No configContext");
    return context;
};