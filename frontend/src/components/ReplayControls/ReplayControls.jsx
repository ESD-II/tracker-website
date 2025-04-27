// src/components/ReplayControls.jsx
import React, { useState, useEffect } from 'react';
import './ReplayControls.css'; // Optional: for styling

// --- Environment URL ---
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function ReplayControls({ onStartReplay, onStopReplay, isPlayingReplay, currentReplayPointId }) {
    const [availablePoints, setAvailablePoints] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    // Fetch available points on mount
    useEffect(() => {
        setIsLoading(true);
        setError(null);

        // *** Construct API URL from environment variable ***
        const apiUrl = `${API_BASE_URL}/api/tracker/points/`;
        console.log(`Fetching points list from: ${apiUrl}`)

        fetch(apiUrl) // Adjust URL if needed
            .then(res => {
                if (!res.ok) {
                    // Log more info on failure
                    return res.text().then(text => {
                       throw new Error(`Failed to fetch points (Status: ${res.status}), Body: ${text}`);
                    });
                }
                return res.json();
            })
            .then(data => {
                setAvailablePoints(data);
                setIsLoading(false);
            })
            .catch(err => {
                console.error("Error fetching points:", err);
                setError(err.message);
                setIsLoading(false);
            });
    // IMPORTANT: No dependencies needed here if API_BASE_URL is constant per build.
    }, []); // Empty dependency array = run once on mount

    return (
        // ... (JSX rendering remains the same) ...
         <div className="replay-controls">
            <h3>Recorded Points</h3>
            {isLoading && <p>Loading points...</p>}
            {error && <p className="error-message">Error loading points: {error}</p>}
            {!isLoading && !error && availablePoints.length === 0 && <p>No points recorded yet.</p>}

            {!isLoading && !error && availablePoints.length > 0 && (
                <ul>
                    {availablePoints.map(point => (
                        <li key={point.id} className={currentReplayPointId === point.id ? 'active' : ''}>
                            <span>
                                Point ID: {point.id} (
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
        </div>
    );
}

export default ReplayControls;