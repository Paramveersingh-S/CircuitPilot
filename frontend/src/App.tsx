import React, { useEffect, useState } from 'react';
import { ChatPanel, ChatMessage } from './components/ChatPanel';
import { BoardCanvas } from './components/BoardCanvas';
import { ActivityFeed } from './components/ActivityFeed';
import { CircuitPilotClient, CircuitPilotEvent, BomItem } from './ws/client';

const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

interface BoardState {
  kicadUrl:    string;
  pythonUrl?:  string;
  pythonCode?: string;
  gerberUrl:   string | null;
  bom:         BomItem[];
  orderLinks:  Record<string, string>;
}

export const App: React.FC = () => {
  const [client,               setClient]               = useState<CircuitPilotClient | null>(null);
  const [events,               setEvents]               = useState<CircuitPilotEvent[]>([]);
  const [chatMessages,         setChatMessages]         = useState<ChatMessage[]>([]);
  const [boardState,           setBoardState]           = useState<BoardState | null>(null);
  const [clarificationOptions, setClarificationOptions] = useState<{id:string; label:string}[]>([]);
  const [isThinking,           setIsThinking]           = useState(false);

  useEffect(() => {
    const c = new CircuitPilotClient(wsUrl);
    setClient(c);

    const unsub = c.onMessage((ev) => {
      setEvents((prev) => [...prev, ev]);

      if (ev.type === 'board_ready') {
        setBoardState({
          kicadUrl:   ev.kicad_url,
          pythonUrl:  ev.python_url,
          pythonCode: ev.python_code,
          gerberUrl:  ev.gerber_url,
          bom:        ev.bom,
          orderLinks: ev.order_links,
        });
        setIsThinking(false);
      } else if (ev.type === 'file_changed') {
        // Backward compat — if board_ready didn't fire, still load the board
        setBoardState(prev => prev ? prev : {
          kicadUrl: ev.path, gerberUrl: null, bom: [], orderLinks: {}
        });
        setIsThinking(false);
      } else if (ev.type === 'chat') {
        setChatMessages((prev) => [...prev, { role: ev.role, text: ev.text, images: ev.images }]);
        if (ev.role === 'assistant') setIsThinking(false);
      } else if (ev.type === 'clarification_options') {
        setClarificationOptions(ev.options);
        setIsThinking(false);
      }
    });

    return () => { unsub(); };
  }, []);

  const handleCommand = (cmd: string, images?: string[]) => {
    if (!client) return;
    setChatMessages((prev) => [...prev, { role: 'user', text: cmd, images }]);
    setClarificationOptions([]);
    setIsThinking(true);
    client.sendCommand(cmd, images);
  };

  return (
    <div className="app-layout">
      <ChatPanel
        onSendCommand={handleCommand}
        messages={chatMessages}
        clarificationOptions={clarificationOptions}
        isThinking={isThinking}
        boardState={boardState}
      />
      <BoardCanvas srcPath={boardState?.kicadUrl} />
      <ActivityFeed events={events} />
    </div>
  );
};
