import React from 'react';

export const ActivityFeed: React.FC<{ events: any[] }> = ({ events }) => {
  return (
    <div className="activity-feed" style={{ width: '300px', borderLeft: '1px solid #ccc', padding: '1rem', overflowY: 'auto' }}>
      <h2>Activity Feed</h2>
      <ul style={{ listStyleType: 'none', padding: 0 }}>
        {events.length === 0 ? (
          <li>No activity yet.</li>
        ) : (
          events.map((ev, idx) => (
            <li key={idx} style={{ marginBottom: '0.5rem', fontSize: '0.9rem' }}>
              <strong style={{ color: '#005571' }}>[{ev.type}]</strong> {ev.text || ev.tool || 'Event recorded'}
            </li>
          ))
        )}
      </ul>
    </div>
  );
};
