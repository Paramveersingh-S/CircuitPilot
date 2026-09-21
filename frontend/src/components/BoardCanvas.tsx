import React, { useEffect, useRef, useState, useCallback } from 'react';

// ─── Zoom/Pan overlay on top of KiCanvas ──────────────────────────────────────
// KiCanvas handles its own internal pan/zoom via mouse, but we also expose
// dedicated +/- buttons, scroll-wheel override, and a "Fit Board" reset button.

export const BoardCanvas: React.FC<{ srcPath?: string }> = ({ srcPath }) => {
  const canvasRef    = useRef<HTMLElement>(null);
  const wrapperRef   = useRef<HTMLDivElement>(null);
  const [zoom, setZoom]   = useState(1.0);
  const [origin, setOrigin] = useState({ x: 0, y: 0 });
  const isPanning    = useRef(false);
  const lastMouse    = useRef({ x: 0, y: 0 });

  // Sync src attribute when board path changes + reset view
  useEffect(() => {
    if (canvasRef.current && srcPath) {
      canvasRef.current.setAttribute('src', srcPath);
    }
    setZoom(1.0);
    setOrigin({ x: 0, y: 0 });
  }, [srcPath]);

  // ── Zoom helpers ──────────────────────────────────────────────────────────
  const clampZoom = (z: number) => Math.min(Math.max(z, 0.15), 10);

  const zoomBy = useCallback((delta: number) => {
    setZoom(z => clampZoom(z + delta));
  }, []);

  const fitBoard = useCallback(() => {
    setZoom(1.0);
    setOrigin({ x: 0, y: 0 });
  }, []);

  // Scroll-wheel zoom (centred on cursor)
  const onWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const factor = e.deltaY > 0 ? -0.08 : 0.08;
    setZoom(z => clampZoom(z + z * factor));
  }, []);

  // ── Pan via middle-mouse or right-mouse drag ──────────────────────────────
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
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '1.5rem', overflow: 'hidden' }}>
      <div className="glass-surface" style={{ flex: 1, display: 'flex', flexDirection: 'column', borderRadius: '1rem', overflow: 'hidden' }}>

        {/* ── Toolbar ─────────────────────────────────────────────────────── */}
        <div style={{
          padding: '0.75rem 1.25rem',
          background: 'rgba(0,0,0,0.25)',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          gap: '0.75rem',
        }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, margin: 0, color: '#fff' }}>
            KiCanvas Workspace
          </h2>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {/* Board name pill */}
            <span style={{
              fontSize: '0.8rem', color: 'var(--text-muted)',
              background: 'rgba(255,255,255,0.06)', padding: '0.2rem 0.7rem',
              borderRadius: '1rem', maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
            }}>
              {srcPath ? `Loaded: ${srcPath.split('/').pop()?.split('?')[0]}` : 'Idle'}
            </span>

            {/* Zoom controls */}
            {srcPath && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                <ZoomBtn onClick={() => zoomBy(-zoom * 0.15)} title="Zoom Out">−</ZoomBtn>

                <span style={{
                  fontSize: '0.78rem', color: 'var(--text-muted)',
                  background: 'rgba(255,255,255,0.06)', padding: '0.2rem 0.5rem',
                  borderRadius: '0.4rem', minWidth: 44, textAlign: 'center', userSelect: 'none',
                }}>
                  {zoomPct}%
                </span>

                <ZoomBtn onClick={() => zoomBy(zoom * 0.15)} title="Zoom In">+</ZoomBtn>
                <ZoomBtn onClick={fitBoard} title="Fit board" style={{ fontSize: '0.7rem', padding: '0.25rem 0.5rem' }}>⤢ Fit</ZoomBtn>
              </div>
            )}
          </div>
        </div>

        {/* ── Canvas Area ──────────────────────────────────────────────────── */}
        <div
          ref={wrapperRef}
          onWheel={onWheel}
          onMouseDown={onMouseDown}
          onMouseMove={onMouseMove}
          onMouseUp={onMouseUp}
          onContextMenu={e => e.preventDefault()}
          style={{
            flex: 1, position: 'relative', background: '#090d14',
            overflow: 'hidden', cursor: isPanning.current ? 'grabbing' : 'default',
          }}
        >
          {srcPath ? (
            <div style={{
              width: '100%', height: '100%',
              transform, transformOrigin: 'center center',
              transition: isPanning.current ? 'none' : 'transform 0.05s ease-out',
              willChange: 'transform',
            }}>
              {/* @ts-ignore — kicanvas-embed is a custom element */}
              <kicanvas-embed
                ref={canvasRef}
                src={srcPath}
                controls="true"
                style={{ width: '100%', height: '100%', border: 'none', display: 'block' }}
              />
            </div>
          ) : (
            <EmptyState />
          )}

          {/* ── Mini zoom hint ────────────────────────────────────────────── */}
          {srcPath && (
            <div style={{
              position: 'absolute', bottom: '0.75rem', left: '50%',
              transform: 'translateX(-50%)',
              fontSize: '0.7rem', color: 'rgba(255,255,255,0.25)',
              pointerEvents: 'none', userSelect: 'none',
            }}>
              Scroll to zoom · Right-click drag to pan
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// ─── Sub-components ────────────────────────────────────────────────────────────
const ZoomBtn: React.FC<{ onClick: () => void; title: string; style?: React.CSSProperties; children: React.ReactNode }> = ({
  onClick, title, style: extraStyle, children,
}) => (
  <button
    onClick={onClick}
    title={title}
    style={{
      background: 'rgba(255,255,255,0.08)',
      border: '1px solid rgba(255,255,255,0.12)',
      color: '#fff',
      borderRadius: '0.4rem',
      width: 28, height: 28,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      cursor: 'pointer',
      fontSize: '1rem', fontWeight: 700,
      transition: 'background 0.15s',
      padding: 0,
      ...extraStyle,
    }}
    onMouseEnter={e => (e.currentTarget.style.background = 'rgba(99,102,241,0.35)')}
    onMouseLeave={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.08)')}
  >
    {children}
  </button>
);

const EmptyState = () => (
  <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', textAlign: 'center', color: 'var(--text-muted)' }}>
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ margin: '0 auto 1rem', opacity: 0.5, display: 'block' }}>
      <path d="M20 7L12 3L4 7M20 7L12 11M20 7V17L12 21M12 11L4 7M12 11V21M4 7V17L12 21" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
    <p style={{ fontSize: '1.1rem', fontWeight: 500, color: '#fff', marginBottom: '0.25rem' }}>No Board Loaded</p>
    <p style={{ fontSize: '0.9rem' }}>Waiting for the layout agent to generate a PCB...</p>
  </div>
);
