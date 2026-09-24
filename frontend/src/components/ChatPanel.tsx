import React, { useState, useEffect, useRef } from 'react';
import type { BomItem } from '../ws/client';

export interface ChatMessage { role: 'user' | 'assistant'; text: string; }

interface BoardState {
  kicadUrl:   string;
  gerberUrl:  string | null;
  bom:        BomItem[];
  orderLinks: Record<string, string>;
}

interface Props {
  onSendCommand:        (cmd: string) => void;
  messages:             ChatMessage[];
  clarificationOptions?: { id: string; label: string }[];
  isThinking?:          boolean;
  boardState?:          BoardState | null;
}

export const ChatPanel: React.FC<Props> = ({
  onSendCommand,
  messages,
  clarificationOptions = [],
  isThinking = false,
  boardState = null,
}) => {
  const [input,      setInput]      = useState('');
  const [showBom,    setShowBom]    = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef  = useRef<HTMLInputElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, clarificationOptions, isThinking, boardState]);

  const handleSend = () => {
    if (!input.trim()) return;
    onSendCommand(input.trim());
    setInput('');
    setShowBom(false);
    inputRef.current?.focus();
  };

  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="panel-header">
        <span className="panel-title">
          <span className="panel-title-dot" />
          CircuitPilot
        </span>
        <span className={`status-badge ${isThinking ? 'loaded' : boardState ? 'ready' : 'idle'}`}>
          {isThinking ? '⏳ Thinking' : boardState ? '✓ Board Ready' : '● Idle'}
        </span>
      </div>

      {/* ── Messages ────────────────────────────────────────────────────── */}
      <div className="chat-scroll" ref={scrollRef}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', marginTop: '32px' }}>
            <div style={{ fontSize: '32px', marginBottom: '12px' }}>🔌</div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: '15px', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Welcome to CircuitPilot
            </div>
            <div style={{ fontSize: '12.5px', color: 'var(--text-muted)', lineHeight: 1.6 }}>
              Describe any circuit in plain English.<br />
              Try: <em style={{ color: 'var(--text-accent)' }}>"ESP32 IoT board with BME280 and USB-C"</em>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`chat-bubble-wrap ${msg.role}`}>
            <div className={`chat-bubble ${msg.role}`}>{msg.text}</div>
          </div>
        ))}

        {isThinking && (
          <div className="chat-bubble-wrap assistant">
            <div className="chat-bubble assistant" style={{ padding: '6px 14px' }}>
              <div className="thinking-dots">
                <span /><span /><span />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Clarification Chips ──────────────────────────────────────────── */}
      {clarificationOptions.length > 0 && (
        <div className="clarification-group">
          {clarificationOptions.map(opt => (
            <button
              key={opt.id}
              className="clarification-chip"
              onClick={() => onSendCommand(opt.label)}
            >
              ↳ {opt.label}
            </button>
          ))}
        </div>
      )}

      {/* ── Board Ready Card ─────────────────────────────────────────────── */}
      {boardState && (
        <>
          <div className="board-ready-card">
            <div className="board-ready-title">
              <span>✓</span> Board Generated
            </div>

            <a href={boardState.kicadUrl} download className="board-action-btn primary">
              <span>⬇</span> Download .kicad_pcb
            </a>

            {boardState.gerberUrl && (
              <a href={boardState.gerberUrl} download className="board-action-btn secondary">
                <span>📦</span> Download Gerbers (ZIP)
              </a>
            )}

            {Object.keys(boardState.orderLinks).length > 0 && (
              <div className="fab-links">
                {Object.entries(boardState.orderLinks).map(([name, url]) => (
                  <a key={name} href={url} target="_blank" rel="noreferrer" className="fab-link">
                    {name.charAt(0).toUpperCase() + name.slice(1)}
                  </a>
                ))}
              </div>
            )}
          </div>

          {/* ── BOM ───────────────────────────────────────────────────────── */}
          {boardState.bom.length > 0 && (
            <div className="bom-section">
              <button className="bom-toggle-btn" onClick={() => setShowBom(v => !v)}>
                {showBom ? '▾' : '▸'} Bill of Materials ({boardState.bom.length} parts)
              </button>
              {showBom && (
                <div style={{ overflowX: 'auto', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', marginTop: '6px' }}>
                  <table className="bom-table">
                    <thead>
                      <tr>
                        <th>Ref</th>
                        <th>Value</th>
                        <th>Cat</th>
                        <th>Buy</th>
                      </tr>
                    </thead>
                    <tbody>
                      {boardState.bom.map((item, i) => (
                        <tr key={i}>
                          <td><span className="bom-ref">{item.reference}</span></td>
                          <td style={{ maxWidth: 110, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.value}</td>
                          <td style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{item.category.split(' ')[0]}</td>
                          <td>
                            <a href={item.source_url} target="_blank" rel="noreferrer" className="bom-link">
                              Octopart ↗
                            </a>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* ── Input ────────────────────────────────────────────────────────── */}
      <div className="chat-input-area">
        <div className="chat-input-row">
          <input
            ref={inputRef}
            id="circuit-prompt-input"
            type="text"
            className="chat-input"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder="Describe a circuit…"
            disabled={isThinking}
          />
          <button
            id="send-prompt-btn"
            className="chat-send-btn"
            onClick={handleSend}
            disabled={isThinking || !input.trim()}
          >
            Generate ↗
          </button>
        </div>
      </div>

      <div className="chat-footer-strip">
        Physics-based routing · IPC-2152 compliant · KiCad native
      </div>
    </div>
  );
};


