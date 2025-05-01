// src/components/ReplayControls.jsx
// This component ALREADY only uses HTTP API calls, no WebSockets/Channels involved.

import React, { useState, useEffect } from 'react';
import './ReplayControls.css'; // Optional: for styling

// --- Environment URL ---
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function ReplayControls({ onStartReplay, onStopReplay, isPlayingReplay, currentReplayPointId }) {
    const [availablePoints, setAvailablePoints] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    // Optional state for pagination links
    // const [nextPageUrl, setNextPageUrl] = useState(null);
    // const [prevPageUrl, setPrevPageUrl] = useState(null);

    useEffect(() => {
        setIsLoading(true);
        setError(null);
        const apiUrl = `${API_BASE_URL}/api/tracker/points/`; // Fetch first page
        console.log(`Fetching points list from: ${apiUrl}`)

        fetch(apiUrl) // Uses standard HTTP fetch
            .then(res => {
                if (!res.ok) {
                    if (res.status === 504) {
                         throw new Error(`Failed to fetch points: Gateway Timeout (Status: ${res.status}). The backend server took too long to respond.`);
                    }
                    return res.text().then(text => {
                       throw new Error(`Failed to fetch points (Status: ${res.status}), Body: ${text}`);
                    });
                }
                return res.json();
            })
            .then(data => {
                // Assumes DRF pagination structure (adjust if not using pagination)
                setAvailablePoints(data.results || data || []); // Use data.results or data itself, fallback to empty array
                // setNextPageUrl(data.next);
                // setPrevPageUrl(data.previous);
                setIsLoading(false);
            })
            .catch(err => {
                console.error("Error fetching points:", err);
                setError(err.message);
                setIsLoading(false);
            });
    }, []); // Empty dependency array = run once on mount

    // Optional function to load more points (example)
    // const loadMorePoints = (url) => { ... };

    return (
        <div className="replay-controls">
            <h3>Recorded Hits</h3>
            {isLoading && <p>Loading...</p>}
            {error && <p className="error-message">Error: {error}</p>}
            {!isLoading && !error && availablePoints.length === 0 && <p>No points recorded yet.</p>}

            {!isLoading && !error && availablePoints.length > 0 && (
                <ul>
                    {availablePoints.map(point => (
                        <li key={point.id} className={currentReplayPointId === point.id ? 'active' : ''}>
                            <span>
                                Hit ID: {point.id} (
                                {new Date(point.recorded_start_time).toLocaleString()}
                                {point.duration_seconds && ` - ${point.duration_seconds.toFixed(1)}s`}
                                )
                            </span>
                            <div className="button-group">
                                <button
                                    onClick={() => onStartReplay(point.id)}
                                    disabled={isPlayingReplay}
                                    className="replay-button"
                                >
                                    Replay
                                </button>
                                {isPlayingReplay && currentReplayPointId === point.id && (
                                    <button
                                        onClick={onStopReplay}
                                        className="stop-button"
                                    >
                                        Stop
                                    </button>
                                )}
                            </div>
                        </li>
                    ))}
                </ul>
            )}
            {/* Optional: Add Load More button
             {!isLoading && nextPageUrl && (
                 <button onClick={() => loadMorePoints(nextPageUrl)}>Load More</button>
             )}
             */}
        </div>
    );
}

export default ReplayControls;