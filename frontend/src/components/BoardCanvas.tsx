import React, { useEffect, useRef, useState, useCallback } from 'react';

export const BoardCanvas: React.FC<{ srcPath?: string }> = ({ srcPath }) => {
  const canvasRef  = useRef<HTMLElement>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const [zoom,   setZoom]   = useState(1.0);
  const [origin, setOrigin] = useState({ x: 0, y: 0 });
  const isPanning  = useRef(false);
  const lastMouse  = useRef({ x: 0, y: 0 });

  useEffect(() => {
    if (canvasRef.current && srcPath) {
      canvasRef.current.setAttribute('src', srcPath);
    }
    setZoom(1.0);
    setOrigin({ x: 0, y: 0 });
  }, [srcPath]);

  const clampZoom = (z: number) => Math.min(Math.max(z, 0.1), 12);

  const zoomBy = useCallback((delta: number) => {
    setZoom(z => clampZoom(z + z * delta));
  }, []);

  const fitBoard = useCallback(() => {
    setZoom(1.0);
    setOrigin({ x: 0, y: 0 });
  }, []);

  const onWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    zoomBy(e.deltaY > 0 ? -0.1 : 0.1);
  }, [zoomBy]);

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button === 1 || e.button === 2) {
      isPanning.current = true;
      lastMouse.current = { x: e.clientX, y: e.clientY };
      e.preventDefault();
    }
  }, []);

  const onMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isPanning.current) return;
    const dx = e.clientX - lastMouse.current.x;
    const dy = e.clientY - lastMouse.current.y;
    lastMouse.current = { x: e.clientX, y: e.clientY };
    setOrigin(o => ({ x: o.x + dx, y: o.y + dy }));
  }, []);

  const onMouseUp = useCallback(() => { isPanning.current = false; }, []);

  const transform = `translate(${origin.x}px, ${origin.y}px) scale(${zoom})`;
  const zoomPct   = Math.round(zoom * 100);

  return (
    <div className="glass-panel" style={{ overflow: 'hidden' }}>

      {/* ── Toolbar ──────────────────────────────────────────────────────── */}
      <div className="panel-header">
        <span className="panel-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ opacity: 0.7 }}>
            <rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/>
          </svg>
          KiCanvas Workspace
        </span>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {srcPath && (
            <span style={{
              fontSize: '11px', color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid var(--border-subtle)',
              padding: '2px 8px', borderRadius: 'var(--radius-sm)',
              maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
            }}>
              {srcPath.split('/').pop()?.split('?')[0]}
            </span>
          )}

          {srcPath && (
            <>
              <button className="zoom-btn" id="zoom-out-btn" onClick={() => zoomBy(-0.15)} title="Zoom Out">−</button>
              <span className="zoom-pct">{zoomPct}%</span>
              <button className="zoom-btn" id="zoom-in-btn" onClick={() => zoomBy(0.15)} title="Zoom In">+</button>
              <button className="zoom-btn" id="fit-board-btn" onClick={fitBoard} title="Fit Board" style={{ width: 'auto', padding: '0 8px', fontSize: '11px' }}>⤢ Fit</button>
            </>
          )}
        </div>
      </div>

      {/* ── Canvas ───────────────────────────────────────────────────────── */}
      <div
        ref={wrapperRef}
        onWheel={onWheel}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onContextMenu={e => e.preventDefault()}
        style={{
          flex: 1,
          position: 'relative',
          background: '#06090f',
          overflow: 'hidden',
          cursor: isPanning.current ? 'grabbing' : 'crosshair',
        }}
      >
        {srcPath ? (
          <div style={{
            width: '100%', height: '100%',
            transform, transformOrigin: 'center center',
            transition: isPanning.current ? 'none' : 'transform 0.06s ease-out',
            willChange: 'transform',
          }}>
            {/* @ts-ignore */}
            <kicanvas-embed
              ref={canvasRef}
              src={srcPath}
              controls="true"
              style={{ width: '100%', height: '100%', border: 'none', display: 'block' }}
            />
          </div>
        ) : (
          <PcbEmptyState />
        )}

        {srcPath && (
          <div style={{
            position: 'absolute', bottom: '12px', left: '50%',
            transform: 'translateX(-50%)',
            fontSize: '10.5px', color: 'rgba(255,255,255,0.2)',
            pointerEvents: 'none', userSelect: 'none',
            fontFamily: 'var(--font-body)',
          }}>
            Scroll to zoom · Right-click drag to pan
          </div>
        )}
      </div>
    </div>
  );
};

const PcbEmptyState = () => (
  <div className="empty-state">
    <svg className="empty-state-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
      <rect x="2" y="2" width="20" height="20" rx="3" strokeDasharray="3 2"/>
      <circle cx="7" cy="7" r="1.5" fill="currentColor" opacity="0.5"/>
      <circle cx="17" cy="7" r="1.5" fill="currentColor" opacity="0.5"/>
      <circle cx="7" cy="17" r="1.5" fill="currentColor" opacity="0.5"/>
      <circle cx="17" cy="17" r="1.5" fill="currentColor" opacity="0.5"/>
      <path d="M7 7h4M13 7h4M7 17h4M13 17h4M7 9v4M17 9v4" strokeLinecap="round"/>
    </svg>
    <div className="empty-state-title">No Board Loaded</div>
    <div className="empty-state-sub">
      Describe your circuit in the chat panel.<br />
      The AI will generate a KiCad PCB here.
    </div>
  </div>
);
