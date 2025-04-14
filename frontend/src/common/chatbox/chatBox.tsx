import { useRef } from 'react';

interface Message {
    role: string;
    text: string;
}

interface ChatFormProps {
    setChatHistory: React.Dispatch<React.SetStateAction<Array<Message>>>;
    generateBotResponse: (messages: Array<Message>) => void;
    chatHistory: Array<Message>;
}

const ConversationList = ({ messages }: { messages: Array<Message> }) => {
    return (
        <div className="flex flex-col gap-4 p-4 overflow-y-auto">
            {messages.map((message, index) => (
                <div
                    key={index}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                    <div
                        className={`max-w-[80%] rounded-lg p-3 ${
                            message.role === 'user'
                                ? 'bg-blue-500 text-white'
                                : 'bg-gray-100 text-gray-800'
                        }`}
                    >
                        <p className="text-sm whitespace-pre-wrap">{message.text}</p>
                        <span className="text-xs opacity-70 mt-1 block">
                            {message.role === 'user' ? 'You' : 'Assistant'}
                        </span>
                    </div>
                </div>
            ))}
        </div>
    );
};

const ChatForm = ({ setChatHistory, generateBotResponse, chatHistory }: ChatFormProps) => {
    const inputRef = useRef<HTMLInputElement>(null);
    
    const handleFormSubmit = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        if (!inputRef.current) return;
        
        const userMessage = inputRef.current.value.trim();
        if (!userMessage) return;
        
        inputRef.current.value = "";
        setChatHistory((history) => [...history, { role: "user", text: userMessage }]);
        
        setTimeout(() => {
            setChatHistory((history) => [...history, { role: "model", text: "Thinking..." }]);
            generateBotResponse([...chatHistory, { role: "user", text: `Using the details provided above, please address this query: ${userMessage}` }]);
        }, 600);
    };

    return (
        <div className="flex flex-col h-full">
            <ConversationList messages={chatHistory} />
            <form onSubmit={handleFormSubmit} className="chat-form p-4 border-t">
                <input ref={inputRef} placeholder="Message..." className="message-input" required />
                <button type="submit" id="send-message" className="material-symbols-rounded">
                    arrow_upward
                </button>
            </form>
        </div>
    );
};

export default ChatForm;