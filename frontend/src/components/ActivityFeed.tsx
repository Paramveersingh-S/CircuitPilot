import React, { useEffect, useRef } from 'react';

export const ActivityFeed: React.FC<{ events: any[] }> = ({ events }) => {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  return (
    <div className="glass-panel" style={{ width: '260px', padding: '1.5rem', display: 'flex', flexDirection: 'column' }}>
      <h2 style={{ fontSize: '1.25rem', fontWeight: 600, letterSpacing: '-0.025em', marginBottom: '1.5rem', color: '#fff' }}>Agent Activity</h2>
      
      <div style={{ flex: 1, overflowY: 'auto', paddingRight: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {events.length === 0 ? (
          <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', fontStyle: 'italic' }}>
            Waiting for tasks...
          </div>
        ) : (
          events.map((ev, idx) => {
            const isTool = ev.type.includes('tool');
            return (
              <div key={idx} className="activity-item glass-surface" style={{ 
                padding: '0.75rem', 
                borderRadius: '0.75rem',
                fontSize: '0.9rem',
                borderLeft: isTool ? '3px solid var(--accent-color)' : '3px solid var(--success-color)'
              }}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginBottom: '0.25rem' }}>
                  <span style={{ 
                    fontSize: '0.75rem', 
                    textTransform: 'uppercase', 
                    letterSpacing: '0.05em', 
                    fontWeight: 600,
                    color: isTool ? 'var(--accent-color)' : 'var(--success-color)' 
                  }}>
                    {ev.type.replace(/_/g, ' ')}
                  </span>
                </div>
                <div style={{ color: 'var(--text-main)', opacity: 0.9 }}>
                  {ev.text || ev.tool || 'Event recorded'}
                </div>
              </div>
            );
          })
        )}
        <div ref={endRef} />
      </div>
    </div>
  );
};
