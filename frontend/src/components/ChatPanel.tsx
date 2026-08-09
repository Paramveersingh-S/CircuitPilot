import React, { useState } from 'react';

export interface ChatMessage { role: 'user' | 'assistant'; text: string; }

export const ChatPanel: React.FC<{ 
  onSendCommand: (cmd: string) => void,
  messages: ChatMessage[] 
}> = ({ onSendCommand, messages }) => {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (!input.trim()) return;
    onSendCommand(input);
    setInput('');
  };

  return (
    <div className="chat-panel" style={{ width: '300px', display: 'flex', flexDirection: 'column', borderRight: '1px solid #ccc', padding: '1rem' }}>
      <h2>Chat Panel</h2>
      <div className="chat-history" style={{ flex: 1, overflowY: 'auto', marginBottom: '1rem' }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ textAlign: msg.role === 'user' ? 'right' : 'left', margin: '0.5rem 0' }}>
            <span style={{ background: msg.role === 'user' ? '#e6f7ff' : '#f0f0f0', padding: '0.5rem', borderRadius: '4px', display: 'inline-block' }}>
              {msg.text}
            </span>
          </div>
        ))}
      </div>
      <div className="chat-input" style={{ display: 'flex' }}>
        <input 
          type="text" 
          value={input} 
          onChange={(e) => setInput(e.target.value)} 
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Describe your circuit..."
          style={{ flex: 1, padding: '0.5rem' }}
        />
        <button onClick={handleSend} style={{ padding: '0.5rem' }}>Send</button>
      </div>
    </div>
  );
};
