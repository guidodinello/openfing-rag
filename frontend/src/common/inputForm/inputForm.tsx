import React, { useState } from "react";

interface InputFormProps {
  onSubmit: (value: string) => void;
  handleKeyPress: (e: React.KeyboardEvent) => void;
}

export const InputForm: React.FC<InputFormProps> = ({
  onSubmit,
  handleKeyPress,
}) => {
  const [value, setValue] = useState("");

  return (
    <div>
      <div>
        <textarea
          placeholder="Ask anything"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyPress}
        />
      </div>
      <div>
        <button
          onClick={() => {
            onSubmit(value);
            setValue("");
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
};
