// src/pages/Replay.jsx (or wherever your Replay component lives)
import React, { useState, useCallback } from 'react';
import TennisCourt3D from '../TennisCourt3D/TennisCourt3D'; // Adjust path if needed
import ReplayControls from '../ReplayControls/ReplayControls'; // Adjust path if needed
import './Replay.css'; // Optional: For page layout styling

function Replay() {
  const [isPlayingReplay, setIsPlayingReplay] = useState(false);
  const [currentReplayPointId, setCurrentReplayPointId] = useState(null);

  // useCallback ensures these functions have stable identities
  // unless their dependencies change (which they don't here)
  const handleStartReplay = useCallback((pointId) => {
    console.log("Replay: Starting replay for point", pointId);
    setCurrentReplayPointId(pointId);
    setIsPlayingReplay(true);
    // The actual fetching and loop start is handled within TennisCourt3D
  }, []);

  const handleStopReplay = useCallback(() => {
    console.log("Replay: Stopping replay");
    setIsPlayingReplay(false);
    setCurrentReplayPointId(null);
    // Resetting state in TennisCourt3D is handled by its useEffect dependencies
  }, []);


  return (
    <main role="main">
      <div className="page-container replay-page-container"> {/* Added class */}
        <h1 className="text-center">Replay Serves / Points</h1>

        {/* --- 3D Visualization Area --- */}
        <TennisCourt3D
          isPlayingReplay={isPlayingReplay}
          pointIdToReplay={currentReplayPointId}
        />

        {/* --- Replay Controls Area --- */}
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