export type Optimistic<T> = T & {
    isOptimistic: true;
};

export const isOptimistic = <T>(
    item: T | Optimistic<T>,
): item is Optimistic<T> => {
    return (
        typeof item === "object" &&
        item !== null &&
        "isOptimistic" in item &&
        item.isOptimistic === true
    );
};
