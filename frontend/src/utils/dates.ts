export const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat("es-ES", {
        hour: "2-digit",
        minute: "2-digit",
    }).format(date);
};

export const formatSecondsToTime = (timestamp: number) =>
    formatTime(new Date(timestamp * 1000));
