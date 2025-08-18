import type { IconType } from "react-icons/lib";
import {
    LuMessageSquare,
    LuBookOpen,
    LuCode,
    LuCalculator,
} from "react-icons/lu";

export interface ExampleQuestion {
    icon: IconType;
    text: string;
    category: string;
}

export const EXAMPLE_QUESTIONS = [
    {
        icon: LuCode,
        text: "¿Cómo se implementa una función recursiva?",
        category: "Programación",
    },
    {
        icon: LuCalculator,
        text: "Explícame el algoritmo de ordenamiento burbuja",
        category: "Algoritmos",
    },
    {
        icon: LuBookOpen,
        text: "¿Qué es la complejidad temporal O(n)?",
        category: "Teoría",
    },
    {
        icon: LuMessageSquare,
        text: "¿Cómo funcionan los punteros en C?",
        category: "Lenguajes",
    },
] as const satisfies ExampleQuestion[];
