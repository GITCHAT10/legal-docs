import React, { useState, useEffect } from 'react';

const MovieCatalog: React.FC = () => {
    const [movies, setMovies] = useState<any[]>([]);

    useEffect(() => {
        // Mock API call to /catalog
        setMovies([
            { id: 'kan-001', title: 'Ocean Tales', available_offline: true },
            { id: 'kan-002', title: 'Island Survival', available_offline: true },
            { id: 'kan-003', title: 'Coral Reefs', available_offline: false }
        ]);
    }, []);

    return (
        <div className="airmovie-catalog">
            <h2>AIRMOVIE EDGE: Available Content</h2>
            <div className="movie-grid" style={{ display: 'flex', gap: '20px' }}>
                {movies.map(movie => (
                    <div key={movie.id} style={{ border: '1px solid #ccc', padding: '10px' }}>
                        <h3>{movie.title}</h3>
                        <p>{movie.available_offline ? '🟢 Available Offline' : '🌐 Online Only'}</p>
                        <button disabled={!movie.available_offline}>Watch Now</button>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default MovieCatalog;
