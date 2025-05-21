import { ReactElement, SetStateAction, useState } from "react";
import { InputForm } from "../../common/inputForm/inputForm";
import ChatForm from "../../common/chatbox/chatBox";

interface Message {
  id: number;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

export const Home = (): ReactElement => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState("");

  const handleSendMessage = (value: string) => {
    if (value.trim()) {
      const message: Message = {
        id: Date.now(),
        text: value,
        isUser: true,
        timestamp: new Date(),
      };
      setMessages([...messages, message]);
      setNewMessage("");
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(newMessage);
    }
  };
  return (
    <>
      <InputForm onSubmit={handleSendMessage} handleKeyPress={handleKeyPress} />
      <ChatForm
        setChatHistory={() => {}}
        generateBotResponse={() => {}}
        chatHistory={[]}
      />
    </>
  );
};
