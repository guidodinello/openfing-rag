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
                <ul className="absolute z-50 mt-1 overflow-y-auto bg-white border border-gray-200 rounded-md shadow-lg max-h-60 ">
                    {options.map((option) => (
                        <li
                            key={option}
                            onClick={() => handleSelect(option)}
                            className="px-4 py-2 cursor-pointer hover:bg-gray-100 whitespace-nowrap"
                        >
                            {option}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};
