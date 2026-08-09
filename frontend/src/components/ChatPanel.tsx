import React, { useState } from 'react';

export const ChatPanel: React.FC = () => {
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState<{role: string, text: string}[]>([]);

    const handleSend = () => {
        if (!input.trim()) return;
        setMessages([...messages, { role: 'user', text: input }]);
        setInput('');
    };

    return (
        <div className="chat-panel">
            <div className="messages">
                {messages.map((m, i) => <div key={i}><strong>{m.role}:</strong> {m.text}</div>)}
            </div>
            <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSend()} />
            <button onClick={handleSend}>Send</button>
        </div>
    );
};
