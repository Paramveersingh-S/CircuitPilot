import React, { useState, useEffect, useRef } from 'react';
import type { BomItem } from '../ws/client';

export interface ChatMessage {
  role: 'user' | 'assistant';
  text: string;
  images?: string[];
}

interface BoardState {
  kicadUrl:    string;
  pythonUrl?:  string;
  pythonCode?: string;
  gerberUrl:   string | null;
  bom:         BomItem[];
  orderLinks:  Record<string, string>;
}

interface Props {
  onSendCommand:         (cmd: string, images?: string[]) => void;
  messages:              ChatMessage[];
  clarificationOptions?: { id: string; label: string }[];
  isThinking?:           boolean;
  boardState?:           BoardState | null;
}

export const ChatPanel: React.FC<Props> = ({
  onSendCommand,
  messages,
  clarificationOptions = [],
  isThinking = false,
  boardState = null,
}) => {
  const [input, setInput] = useState('');
  const [showBom, setShowBom] = useState(false);
  const [showPythonModal, setShowPythonModal] = useState(false);
  const [copiedCode, setCopiedCode] = useState(false);
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [attachedImages, setAttachedImages] = useState<{ id: string; name: string; dataUrl: string }[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, clarificationOptions, isThinking, boardState, attachedImages]);

  const handleFiles = (files: FileList | File[]) => {
    const fileArr = Array.from(files);
    fileArr.forEach((file) => {
      if (!file.type.startsWith('image/')) return;
      const reader = new FileReader();
      reader.onload = (e) => {
        const dataUrl = e.target?.result as string;
        if (dataUrl) {
          setAttachedImages((prev) => [
            ...prev,
            { id: Math.random().toString(36).substring(7), name: file.name, dataUrl }
          ]);
        }
      };
      reader.readAsDataURL(file);
    });
  };

  const removeAttachedImage = (id: string) => {
    setAttachedImages((prev) => prev.filter((img) => img.id !== id));
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    const imgFiles: File[] = [];
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf('image') !== -1) {
        const file = items[i].getAsFile();
        if (file) imgFiles.push(file);
      }
    }
    if (imgFiles.length > 0) {
      e.preventDefault();
      handleFiles(imgFiles);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer?.files) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed && attachedImages.length === 0) return;

    const promptText = trimmed || 'Generate KiCad PCB circuit and copper paths for the attached diagram';
    const imagesPayload = attachedImages.map((img) => img.dataUrl);

    onSendCommand(promptText, imagesPayload);
    setInput('');
    setAttachedImages([]);
    setShowBom(false);
    inputRef.current?.focus();
  };

  const copyPythonCode = () => {
    if (boardState?.pythonCode) {
      navigator.clipboard.writeText(boardState.pythonCode);
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2000);
    }
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
          {isThinking ? '⏳ Generating' : boardState ? '✓ Board Ready' : '● Idle'}
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
              Describe any circuit in plain English or <strong style={{ color: 'var(--text-accent)' }}>attach a schematic image</strong>.<br />
              Try: <em style={{ color: 'var(--text-accent)' }}>"555 timer LED flasher with 9V input"</em>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`chat-bubble-wrap ${msg.role}`}>
            <div className={`chat-bubble ${msg.role}`}>
              {msg.images && msg.images.length > 0 && (
                <div className="msg-images-grid">
                  {msg.images.map((imgUrl, imgIdx) => (
                    <img
                      key={imgIdx}
                      src={imgUrl}
                      alt="Circuit schematic / diagram"
                      className="msg-attached-img"
                      onClick={() => setPreviewImage(imgUrl)}
                      title="Click to view full image"
                    />
                  ))}
                </div>
              )}
              {msg.text}
            </div>
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
              <span>✓</span> KiCad PCB & Python Code Generated
            </div>

            <a href={boardState.kicadUrl} download className="board-action-btn primary">
              <span>⬇</span> Download .kicad_pcb
            </a>

            {boardState.pythonUrl && (
              <a href={boardState.pythonUrl} download="circuit_generator.py" className="board-action-btn python-btn">
                <span>🐍</span> Download Python Script (.py)
              </a>
            )}

            {boardState.pythonCode && (
              <button
                className="board-action-btn view-code-btn"
                onClick={() => setShowPythonModal(true)}
              >
                <span>🔍</span> View Python Generator Code
              </button>
            )}

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

      {/* ── Attached Images Tray ─────────────────────────────────────────── */}
      {attachedImages.length > 0 && (
        <div className="attached-images-tray">
          {attachedImages.map((img) => (
            <div key={img.id} className="attached-img-card">
              <img src={img.dataUrl} alt={img.name} className="attached-img-thumb" />
              <span className="attached-img-name" title={img.name}>{img.name}</span>
              <button
                type="button"
                className="attached-img-remove"
                onClick={() => removeAttachedImage(img.id)}
                title="Remove image"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      {/* ── Input ────────────────────────────────────────────────────────── */}
      <div
        className="chat-input-area"
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
      >
        <div className={`chat-input-row ${isDragOver ? 'drag-over' : ''}`} onPaste={handlePaste}>
          {/* Hidden File Input */}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            multiple
            style={{ display: 'none' }}
            onChange={(e) => {
              if (e.target.files) handleFiles(e.target.files);
              e.target.value = '';
            }}
          />

          {/* Attach Image Button */}
          <button
            type="button"
            className="chat-attach-btn"
            onClick={() => fileInputRef.current?.click()}
            title="Attach circuit schematic / diagram image (or drag & drop / paste)"
            disabled={isThinking}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <circle cx="8.5" cy="8.5" r="1.5"/>
              <polyline points="21 15 16 10 5 21"/>
            </svg>
          </button>

          <input
            ref={inputRef}
            id="circuit-prompt-input"
            type="text"
            className="chat-input"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder={attachedImages.length > 0 ? "Describe circuit or press Generate..." : "Describe circuit or attach schematic…"}
            disabled={isThinking}
          />
          <button
            id="send-prompt-btn"
            className="chat-send-btn"
            onClick={handleSend}
            disabled={isThinking || (!input.trim() && attachedImages.length === 0)}
          >
            Generate ↗
          </button>
        </div>
      </div>

      <div className="chat-footer-strip">
        Python .py script generator · 45° chamfered copper paths · KiCad native
      </div>

      {/* ── Python Code Modal ────────────────────────────────────────────── */}
      {showPythonModal && boardState?.pythonCode && (
        <div className="code-modal-overlay" onClick={() => setShowPythonModal(false)}>
          <div className="code-modal" onClick={e => e.stopPropagation()}>
            <div className="code-modal-header">
              <div className="code-modal-title">
                <span>🐍</span> KiCad PCB Generator (circuit_generator.py)
              </div>
              <div className="code-modal-actions">
                <button className="modal-action-btn" onClick={copyPythonCode}>
                  {copiedCode ? '✓ Copied!' : '📋 Copy Code'}
                </button>
                {boardState.pythonUrl && (
                  <a
                    href={boardState.pythonUrl}
                    download="circuit_generator.py"
                    className="modal-action-btn"
                    style={{ textDecoration: 'none' }}
                  >
                    ⬇ Download .py
                  </a>
                )}
                <button className="modal-action-btn" onClick={() => setShowPythonModal(false)}>
                  ✕
                </button>
              </div>
            </div>
            <div className="code-modal-body">
              <pre className="code-viewer">
                <code>{boardState.pythonCode}</code>
              </pre>
            </div>
          </div>
        </div>
      )}

      {/* ── Image Lightbox Modal ─────────────────────────────────────────── */}
      {previewImage && (
        <div className="img-lightbox-overlay" onClick={() => setPreviewImage(null)}>
          <img src={previewImage} alt="Full circuit diagram" className="lightbox-img" onClick={e => e.stopPropagation()} />
        </div>
      )}
    </div>
  );
};
