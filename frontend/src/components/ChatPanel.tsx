import React, { useState, useEffect, useRef } from 'react';

export interface ChatMessage { role: 'user' | 'assistant'; text: string; }

export const ChatPanel: React.FC<{ 
  onSendCommand: (cmd: string) => void,
  messages: ChatMessage[],
  clarificationOptions?: {id: string, label: string}[]
}> = ({ onSendCommand, messages, clarificationOptions = [] }) => {
  const [input, setInput] = useState('');
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, clarificationOptions]);

  const handleSend = () => {
    if (!input.trim()) return;
    onSendCommand(input);
    setInput('');
  };

  return (
    <div className="glass-panel" style={{ width: '380px', display: 'flex', flexDirection: 'column', padding: '1.5rem' }}>
      <h2 style={{ fontSize: '1.25rem', fontWeight: 600, letterSpacing: '-0.025em', marginBottom: '1.5rem', color: '#fff' }}>CircuitPilot Assistant</h2>
      
      <div className="chat-history" style={{ flex: 1, overflowY: 'auto', marginBottom: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem', paddingRight: '0.5rem' }}>
        {messages.length === 0 && (
          <div style={{ margin: 'auto', color: 'var(--text-muted)', textAlign: 'center', fontSize: '0.9rem' }}>
            <p>Welcome to CircuitPilot.</p>
            <p>Try asking: "Create a 5V buck converter"</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className="chat-message" style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div style={{ 
              background: msg.role === 'user' ? 'linear-gradient(135deg, #3b82f6, #2563eb)' : 'var(--bg-surface)', 
              color: '#fff',
              padding: '0.75rem 1rem', 
              borderRadius: msg.role === 'user' ? '1rem 1rem 0 1rem' : '1rem 1rem 1rem 0',
              maxWidth: '85%',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              fontSize: '0.95rem',
              lineHeight: '1.4'
            }}>
              {msg.text}
            </div>
          </div>
        ))}
        
        {clarificationOptions.length > 0 && (
          <div className="chat-message" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.5rem' }}>
            {clarificationOptions.map(opt => (
              <button 
                key={opt.id}
                onClick={() => onSendCommand(opt.label)}
                style={{
                  background: 'rgba(59, 130, 246, 0.15)',
                  border: '1px solid var(--accent-color)',
                  color: '#fff',
                  padding: '0.6rem 1rem',
                  borderRadius: '0.5rem',
                  cursor: 'pointer',
                  textAlign: 'left',
                  fontSize: '0.9rem',
                  transition: 'all 0.2s ease',
                }}
                onMouseOver={(e) => e.currentTarget.style.background = 'rgba(59, 130, 246, 0.3)'}
                onMouseOut={(e) => e.currentTarget.style.background = 'rgba(59, 130, 246, 0.15)'}
              >
                {opt.label}
              </button>
            ))}
          </div>
        )}
        
        <div ref={endRef} />
      </div>

      <div className="chat-input" style={{ display: 'flex', gap: '0.5rem', background: 'var(--bg-surface)', padding: '0.5rem', borderRadius: '0.75rem', border: '1px solid var(--border-color)' }}>
        <input 
          type="text" 
          value={input} 
          onChange={(e) => setInput(e.target.value)} 
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Design a circuit..."
          style={{ flex: 1, padding: '0.5rem 0.75rem', background: 'transparent', border: 'none', color: '#fff', outline: 'none', fontSize: '0.95rem' }}
        />
        <button 
          onClick={handleSend} 
          style={{ 
            background: 'var(--accent-color)', 
            color: '#fff', 
            border: 'none', 
            padding: '0.5rem 1.25rem', 
            borderRadius: '0.5rem',
            cursor: 'pointer',
            fontWeight: 500
          }}>
          Send
        </button>
      </div>
    </div>
  );
};
