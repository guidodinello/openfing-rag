export const floatToPercentage = (value: number) => {
    return parseFloat((value * 100).toFixed(1));
};

// Sources carry raw pgvector cosine distance (0 = identical, 2 = opposite).
// Convert to cosine similarity (higher = more relevant) for display purposes.
export const cosineDistanceToSimilarity = (distance: number) => 1 - distance;
