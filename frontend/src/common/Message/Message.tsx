enum MessageRole {
    USER = "user",
    Model = "Model",
}

interface MessageProps {
    role: MessageRole;
    text: string;
}

export const Message = ({ role, text }: MessageProps) => {
    return (
        <div className="flex flex-col gap-2" style={{ justifyContent: role === MessageRole.USER ? "flex-end" : "flex-start" }} >
            <h1>{text}</h1>
        </div>
    );
};
