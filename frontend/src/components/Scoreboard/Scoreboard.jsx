// src/components/Scoreboard.jsx
import React from 'react';
import './Scoreboard.css'; // Optional: Create this file for styling

// Helper to format points (e.g., handle AD)
const formatPoint = (point) => {
    return point === null || point === undefined ? '0' : String(point);
};

// Helper to format games/sets
const formatGame = (game) => {
    return game === null || game === undefined ? 0 : Number(game);
};

function Scoreboard({
    team1Points,
    team2Points,
    team1Games,
    team2Games,
    currentSet,
    serverPlayer, // Optional: 1 or 2 to indicate server
}) {
    // Determine which player has the serve indicator (optional)
    const isPlayer1Serving = serverPlayer === 1;
    const isPlayer2Serving = serverPlayer === 2;

    return (
        <div className="scoreboard">
            <div className="scoreboard-header">
                <span>Set {formatGame(currentSet)}</span>
                {/* Add Clock here later if needed */}
            </div>
            <div className="scoreboard-row player1">
                <span className={`player-name ${isPlayer1Serving ? 'serving' : ''}`}>
                    Player 1 {isPlayer1Serving && '🎾'}
                </span>
                <span className="games">{formatGame(team1Games)}</span>
                <span className="points">{formatPoint(team1Points)}</span>
            </div>
            <div className="scoreboard-row player2">
                <span className={`player-name ${isPlayer2Serving ? 'serving' : ''}`}>
                    Player 2 {isPlayer2Serving && '🎾'}
                </span>
                <span className="games">{formatGame(team2Games)}</span>
                <span className="points">{formatPoint(team2Points)}</span>
            </div>
        </div>
    );
}

export default Scoreboard;