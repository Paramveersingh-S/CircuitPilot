import React, { useEffect, useState } from 'react';
import { ChatPanel } from './components/ChatPanel';
import { BoardCanvas } from './components/BoardCanvas';
import { ActivityFeed } from './components/ActivityFeed';
import { CircuitPilotClient, CircuitPilotEvent } from './ws/client';

const wsUrl = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws";

export const App: React.FC = () => {
  const [client, setClient] = useState<CircuitPilotClient | null>(null);
  const [events, setEvents] = useState<CircuitPilotEvent[]>([]);
  const [chatMessages, setChatMessages] = useState<{role: 'user'|'assistant', text: string}[]>([]);
  const [boardSrc, setBoardSrc] = useState<string>('');

  useEffect(() => {
    const newClient = new CircuitPilotClient(wsUrl);
    setClient(newClient);

    const unsubscribe = newClient.onMessage((ev) => {
      setEvents((prev) => [...prev, ev]);
      if (ev.type === 'file_changed') {
        setBoardSrc(ev.path);
      } else if (ev.type === 'chat') {
        setChatMessages((prev) => [...prev, { role: ev.role, text: ev.text }]);
      }
    });

    return () => {
      unsubscribe();
    };
  }, []);

  const handleCommand = (cmd: string) => {
    if (client) {
      setChatMessages((prev) => [...prev, { role: 'user', text: cmd }]);
      client.sendCommand(cmd);
    }
  };

  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'sans-serif' }}>
      <ChatPanel onSendCommand={handleCommand} messages={chatMessages} />
      <BoardCanvas srcPath={boardSrc} />
      <ActivityFeed events={events} />
    </div>
  );
};
