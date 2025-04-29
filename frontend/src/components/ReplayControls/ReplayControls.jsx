// src/components/ReplayControls.jsx
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

        fetch(apiUrl)
            .then(res => {
                if (!res.ok) {
                    // Provide more specific error message for gateway timeout
                    if (res.status === 504) {
                         throw new Error(`Failed to fetch points: Gateway Timeout (Status: ${res.status}). The backend server took too long to respond.`);
                    }
                     // Try to get more info from the response body for other errors
                    return res.text().then(text => {
                       throw new Error(`Failed to fetch points (Status: ${res.status}), Body: ${text}`);
                    });
                }
                return res.json();
            })
            .then(data => {
                // *** THIS IS THE KEY CHANGE ***
                // Access the 'results' array from the paginated response object
                setAvailablePoints(data.results || []); // Use data.results, fallback to empty array

                // Optional: Store pagination links if you want to implement Load More later
                // setNextPageUrl(data.next);
                // setPrevPageUrl(data.previous);

                setIsLoading(false);
            })
            .catch(err => {
                console.error("Error fetching points:", err);
                setError(err.message); // Display the specific error message
                setIsLoading(false);
            });
    }, []); // Empty dependency array = run once on mount

    // Optional function to load more points (example)
    // const loadMorePoints = (url) => {
    //     if (!url) return;
    //     setIsLoading(true);
    //     fetch(url)
    //         .then(res => res.ok ? res.json() : Promise.reject('Failed to fetch next page'))
    //         .then(data => {
    //             setAvailablePoints(prevPoints => [...prevPoints, ...(data.results || [])]); // Append results
    //             setNextPageUrl(data.next);
    //             setPrevPageUrl(data.previous);
    //             setIsLoading(false);
    //         })
    //         .catch(err => {
    //             console.error("Error loading more points:", err);
    //             setError(typeof err === 'string' ? err : 'Could not load more points.');
    //             setIsLoading(false);
    //         });
    // };

    return (
        <div className="replay-controls">
            <h3>Recorded Points</h3>
            {isLoading && <p>Loading...</p>} {/* Simplified loading message */}
            {error && <p className="error-message">Error: {error}</p>} {/* Display specific error */}
            {!isLoading && !error && availablePoints.length === 0 && <p>No points recorded yet.</p>}

            {!isLoading && !error && availablePoints.length > 0 && (
                <ul>
                    {/* Now mapping over the first page of results */}
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
            {/* Optional: Add Load More button
             {!isLoading && nextPageUrl && (
                 <button onClick={() => loadMorePoints(nextPageUrl)}>Load More</button>
             )}
             */}
        </div>
    );
}

export default ReplayControls;