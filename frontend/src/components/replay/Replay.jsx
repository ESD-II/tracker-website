// src/pages/Replay.jsx
import React, { useState, useCallback } from 'react';
import TennisCourt3D from '../TennisCourt3D/TennisCourt3D'; // Adjust path if needed
import ReplayControls from '../ReplayControls/ReplayControls'; // Adjust path if needed
import './Replay.css'; // Optional: For page layout styling

function Replay() {
  // State variables remain the same
  const [isPlayingReplay, setIsPlayingReplay] = useState(false);
  const [currentReplayPointId, setCurrentReplayPointId] = useState(null);

  // Callbacks remain the same
  const handleStartReplay = useCallback((pointId) => {
    console.log("Replay Page: Starting replay for point", pointId);
    setCurrentReplayPointId(pointId);
    setIsPlayingReplay(true);
  }, []);

  const handleStopReplay = useCallback(() => {
    console.log("Replay Page: Stopping replay");
    setIsPlayingReplay(false);
    setCurrentReplayPointId(null);
  }, []);


  return (
    <main role="main">
      <div className="page-container replay-page-container">
        <h1 className="text-center">Replay Serves / Points</h1>

        {/* --- 3D Visualization Area --- */}
        {/* *** CORRECTED PROP NAMES BELOW *** */}
        <TennisCourt3D
          isReplayActive={isPlayingReplay}     // Pass state 'isPlayingReplay' as prop 'isReplayActive'
          replayPointId={currentReplayPointId} // Pass state 'currentReplayPointId' as prop 'replayPointId'
        />

        {/* --- Replay Controls Area --- */}
        {/* Props passed to ReplayControls seem correct based on its definition */}
        <ReplayControls
            onStartReplay={handleStartReplay}
            onStopReplay={handleStopReplay}
            isPlayingReplay={isPlayingReplay}
            currentReplayPointId={currentReplayPointId}
        />

      </div>
    </main>
  );
}

export default Replay;