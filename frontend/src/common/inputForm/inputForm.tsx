import React, { useState } from 'react';
import './inputForm.css';

interface InputFormProps {
    onSubmit: (value: string) => void;
}

export const InputForm: React.FC<InputFormProps> = ({ onSubmit }) => {
    const [value, setValue] = useState('');

    return (
        <div className="input-form-container">
            <div className="input-wrapper">
                <textarea
                    className="chat-input"
                    placeholder="Ask anything"
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                />
            </div>
            <div className="button-container">
                <button
                    onClick={() => {
                        onSubmit(value);
                        setValue('');
                    }}
                    className="send-button"
                >
                    Send
                </button>
            </div>
        </div>
    );
};



