import React, { useEffect, useRef } from 'react';

export const BoardCanvas: React.FC<{ srcPath?: string }> = ({ srcPath }) => {
  const canvasRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (canvasRef.current && srcPath) {
      canvasRef.current.setAttribute('src', srcPath);
    }
  }, [srcPath]);

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '1.5rem', overflow: 'hidden' }}>
      <div className="glass-surface" style={{ flex: 1, display: 'flex', flexDirection: 'column', borderRadius: '1rem', overflow: 'hidden' }}>
        
        <div style={{ padding: '1rem 1.5rem', background: 'rgba(0,0,0,0.2)', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, margin: 0, color: '#fff' }}>KiCanvas Workspace</h2>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', background: 'rgba(255,255,255,0.05)', padding: '0.25rem 0.75rem', borderRadius: '1rem' }}>
            {srcPath ? `Loaded: ${srcPath.split('/').pop()}` : "Idle"}
          </span>
        </div>
        
        <div style={{ flex: 1, position: 'relative', background: '#090d14' }}>
          {srcPath ? (
            <kicanvas-embed ref={canvasRef} src={srcPath} controls="true" style={{ width: '100%', height: '100%', border: 'none', display: 'block' }}></kicanvas-embed>
          ) : (
            <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', textAlign: 'center', color: 'var(--text-muted)' }}>
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ margin: '0 auto 1rem', opacity: 0.5 }}>
                <path d="M20 7L12 3L4 7M20 7L12 11M20 7V17L12 21M12 11L4 7M12 11V21M4 7V17L12 21" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <p style={{ fontSize: '1.1rem', fontWeight: 500, color: '#fff', marginBottom: '0.25rem' }}>No Board Loaded</p>
              <p style={{ fontSize: '0.9rem' }}>Waiting for the layout agent to generate a PCB...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
