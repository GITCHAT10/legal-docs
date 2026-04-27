import React from 'react';

const VideoPlayer: React.FC<{ movieId: string, manifestUrl: string, watermark: string }> = ({ movieId, manifestUrl, watermark }) => {
    return (
        <div className="airmovie-player" style={{ position: 'relative', width: '800px', height: '450px', background: '#000' }}>
            <div style={{ position: 'absolute', top: '20px', left: '20px', color: 'rgba(255,255,255,0.3)', pointerEvents: 'none' }}>
                {watermark}
            </div>
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', color: '#fff' }}>
                <p>Playing: {movieId}</p>
                <p style={{ fontSize: '12px', marginLeft: '10px' }}>({manifestUrl})</p>
            </div>
        </div>
    );
};

export default VideoPlayer;
