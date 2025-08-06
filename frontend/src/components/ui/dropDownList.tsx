import { useState, useRef, useEffect } from "react";

interface DropdownProps<T extends string | number> {
    options: T[];
    onSelect: (value: T) => void;
    selectedValue: T;
    disabled: boolean;
}

export const DropDownList = <T extends string | number>({
    options,
    onSelect,
    selectedValue,
    disabled,
}: DropdownProps<T>) => {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    const handleToggle = () => {
        setIsOpen((prev) => !prev);
    };

    const handleSelect = (value: T) => {
        onSelect(value);
        setIsOpen(false);
    };

    const handleClickOutside = (event: MouseEvent) => {
        if (
            dropdownRef.current &&
            !dropdownRef.current.contains(event.target as Node)
        ) {
            setIsOpen(false);
        }
    };

    useEffect(() => {
        document.addEventListener("mousedown", handleClickOutside);
        return () =>
            document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    return (
        <div
            ref={dropdownRef}
            style={{ position: "relative", display: "inline-block" }}
        >
            <button onClick={handleToggle} disabled={disabled}>
                {selectedValue} ▼
            </button>
            {isOpen && (
                <ul
                    style={{
                        position: "absolute",
                        margin: 0,
                        padding: "0.5rem",
                        listStyle: "none",
                        border: "1px solid #ccc",
                        backgroundColor: "#fff",
                        zIndex: 1000,
                    }}
                >
                    {options.map((option) => (
                        <li
                            key={option}
                            onClick={() => handleSelect(option)}
                            style={{
                                padding: "0.25rem 0.5rem",
                                cursor: "pointer",
                            }}
                        >
                            {option}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};
