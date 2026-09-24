import React, { useEffect, useRef } from 'react';

export const ActivityFeed: React.FC<{ events: any[] }> = ({ events }) => {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  const getTypeClass = (type: string) => {
    if (type === 'chat')               return 'type-chat';
    if (type === 'file_changed')       return 'type-file_changed';
    if (type === 'board_ready')        return 'type-board_ready';
    if (type.includes('error'))        return 'type-error';
    return 'type-other';
  };

  const getLabel = (ev: any) => {
    if (ev.type === 'chat')         return ev.text?.slice(0, 90) || 'Chat message';
    if (ev.type === 'file_changed') return `PCB loaded: ${ev.path?.split('/').pop()?.split('?')[0] || ''}`;
    if (ev.type === 'board_ready')  return `Board + BOM ready (${ev.bom?.length ?? 0} parts)`;
    if (ev.type === 'tool_call_started')   return `🔧 ${ev.tool}`;
    if (ev.type === 'tool_call_completed') return `✓ ${ev.tool || 'Tool done'}`;
    if (ev.type === 'drc_result')   return ev.clean ? '✓ DRC passed (0 violations)' : `⚠ DRC: ${ev.violations?.length} violations`;
    return ev.text || ev.tool || ev.type;
  };

  return (
    <div className="glass-panel">
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="panel-header">
        <span className="panel-title">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ opacity: 0.7 }}>
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" strokeLinejoin="round" strokeLinecap="round"/>
          </svg>
          Agent Activity
        </span>
        {events.length > 0 && (
          <span style={{
            fontSize: '10px', fontWeight: 700,
            background: 'rgba(255,255,255,0.06)',
            color: 'var(--text-muted)',
            padding: '2px 7px', borderRadius: '100px',
          }}>
            {events.length}
          </span>
        )}
      </div>

      {/* ── Events ──────────────────────────────────────────────────────── */}
      <div className="activity-scroll">
        {events.length === 0 ? (
          <div style={{
            textAlign: 'center', paddingTop: '32px',
            color: 'var(--text-muted)', fontSize: '12.5px',
          }}>
            <div style={{ fontSize: '24px', marginBottom: '8px', opacity: 0.4 }}>⚡</div>
            Waiting for agent activity…
          </div>
        ) : (
          events.map((ev, idx) => (
            <div key={idx} className={`activity-item ${getTypeClass(ev.type)}`}>
              <div className="activity-type-label">{ev.type.replace(/_/g, ' ')}</div>
              <div className="activity-text">{getLabel(ev)}</div>
            </div>
          ))
        )}
        <div ref={endRef} />
      </div>
    </div>
  );
};

