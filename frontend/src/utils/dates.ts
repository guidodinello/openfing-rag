export const formatToLocalTime = (date: Date) => {
    return new Intl.DateTimeFormat("es-ES", {
        hour: "2-digit",
        minute: "2-digit",
    }).format(date);
};

export const formatSecondsToTimeWithHours = (totalSeconds: number): string => {
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = Math.floor(totalSeconds % 60);

    return `${hours.toString().padStart(2, "0")}:${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
};
