import React, { useEffect, useRef } from 'react';

export const BoardCanvas: React.FC<{ srcPath?: string }> = ({ srcPath }) => {
  const canvasRef = useRef<HTMLElement>(null);

  useEffect(() => {
    // If we had the actual kicanvas element, we'd update its source here.
    if (canvasRef.current && srcPath) {
      canvasRef.current.setAttribute('src', srcPath);
    }
  }, [srcPath]);

  return (
    <div className="board-canvas" style={{ flex: 1, border: '1px solid #ccc' }}>
      <h2>KiCanvas Board View</h2>
      {/* 
        This is the official custom element from @theacodes/kicanvas
        <kicanvas-embed ref={canvasRef} src={srcPath || "/default.kicad_pcb"} controls="true"></kicanvas-embed> 
      */}
      <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
        Interactive Board View (KiCanvas will render here when a board is loaded)
      </div>
    </div>
  );
};
