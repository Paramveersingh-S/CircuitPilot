with open("backend/app/agent/tools/ato_tools.py", "w") as f:
    f.write("""def ato_search_package(query: str):
    pass

def ato_add_module(target_file: str, module_name: str, package_ref: str, inline_spec: str):
    pass

def ato_set_parameter(module_id: str, param: str, value: float, unit: str, tolerance: float):
    pass

def ato_connect(a: str, b: str):
    pass

def ato_build(target_file: str):
    pass
""")

with open("backend/app/agent/orchestrator.py", "w") as f:
    f.write("""class Orchestrator:
    def __init__(self):
        self.planner = None
        self.agents = {}
        
    async def handle_command(self, session, user_text: str):
        pass
""")

with open("backend/app/ws/events.py", "w") as f:
    f.write("""from pydantic import BaseModel

class ChatEvent(BaseModel):
    type: str = "chat"
    role: str
    text: str

class FileChangedEvent(BaseModel):
    type: str = "file_changed"
    path: str
    ts: str
""")

with open("frontend/src/components/ChatPanel.tsx", "w") as f:
    f.write("""import React, { useState } from 'react';

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
""")
