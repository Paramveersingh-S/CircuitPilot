import React, { useEffect, useRef } from 'react';

export const BoardCanvas: React.FC<{ fileUrl: string }> = ({ fileUrl }) => {
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // KiCanvas initialization logic
        if (containerRef.current) {
            containerRef.current.innerHTML = `<kicanvas-embed src="${fileUrl}"></kicanvas-embed>`;
        }
    }, [fileUrl]);

    return <div ref={containerRef} style={{ width: '100%', height: '100%' }} />;
};
