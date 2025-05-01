// src/pages/Replay.jsx
import React, { useState, useCallback, useEffect } from 'react';
import TennisCourt3D from '../TennisCourt3D/TennisCourt3D';
import ReplayControls from '../ReplayControls/ReplayControls';
import './Replay.css';

// Example internal "ad" data (Ensure these arrays are not empty)
const leftAds = [
  { id: 'left1', type: 'image', src: '/raidShadowLegends.jpg', alt: 'Raid Shadow Legends Ad', link: '#' },
  { id: 'left2', type: 'image', src: 'https://via.placeholder.com/160x600/eee/888?text=Sponsor+A', alt: 'Sponsor A', link: '#' },
  { id: 'left3', type: 'text', text: 'Check out our new features!' },
];
const rightAds = [
  { id: 'right1', type: 'image', src: 'https://placehold.co/160x600/orange/white?text=Right+Ad+1', alt: 'Right Ad 1', link: '#' },
  { id: 'right2', type: 'text', text: 'Support the Project!' },
  { id: 'right3', type: 'image', src: 'https://placehold.co/160x600/000/fff?text=Sponsor+B', alt: 'Sponsor B', link: '#' },
];

const AD_ROTATION_INTERVAL = 5000;

function Replay() {
  const [isPlayingReplay, setIsPlayingReplay] = useState(false);
  const [currentReplayPointId, setCurrentReplayPointId] = useState(null);
  const [leftAdIndex, setLeftAdIndex] = useState(0);
  const [rightAdIndex, setRightAdIndex] = useState(0);

  // Callbacks
  const handleStartReplay = useCallback((pointId) => { setIsPlayingReplay(true); setCurrentReplayPointId(pointId); }, []);
  const handleStopReplay = useCallback(() => { setIsPlayingReplay(false); setCurrentReplayPointId(null); }, []);

  // Effect for rotating ads
  useEffect(() => {
    // Check if arrays have content before setting interval
    if (leftAds.length === 0 && rightAds.length === 0) return;

    const intervalId = setInterval(() => {
      if (leftAds.length > 0) {
        setLeftAdIndex(prevIndex => (prevIndex + 1) % leftAds.length);
      }
      if (rightAds.length > 0) {
        setRightAdIndex(prevIndex => (prevIndex + 1) % rightAds.length);
      }
    }, AD_ROTATION_INTERVAL);

    return () => clearInterval(intervalId);
  }, []); // Dependencies are empty, runs once

  // Get current ads safely
  // Provide a default object if the array is empty or index is out of bounds (shouldn't happen with %)
  const currentLeftAd = leftAds.length > 0 ? leftAds[leftAdIndex] : null;
  const currentRightAd = rightAds.length > 0 ? rightAds[rightAdIndex] : null;

  return (
    <div className="replay-page-content">
      <h1 className="text-center">Replay Hit</h1>
      <div className="replay-layout-container">
        {/* --- Left Sidebar --- */}
        <aside className="replay-sidebar replay-sidebar-left">
          <h4>Sponsor Area</h4>
          {/* *** ADD CHECK: Ensure currentLeftAd exists before accessing .type *** */}
          {currentLeftAd && currentLeftAd.type === 'image' && (
            <a href={currentLeftAd.link || '#'} target="_blank" rel="noopener noreferrer">
               <img src={currentLeftAd.src} alt={currentLeftAd.alt} width="160" height="600" />
            </a>
          )}
          {/* *** ADD CHECK: Ensure currentLeftAd exists before accessing .type *** */}
          {currentLeftAd && currentLeftAd.type === 'text' && (
             <div style={{ border: '1px dashed grey', width: '160px', height: '600px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#eee', padding: '5px', textAlign:'center' }}>
               {currentLeftAd.text}
             </div>
          )}
          {/* Optional: Placeholder if no ad */}
          {!currentLeftAd && (
             <div style={{ width: '160px', height: '600px', background: '#ddd' }}></div>
          )}
        </aside>

        {/* --- Center Content Area --- */}
        <section className="replay-center-content">
           <TennisCourt3D isReplayActive={isPlayingReplay} replayPointId={currentReplayPointId} />
           <ReplayControls onStartReplay={handleStartReplay} onStopReplay={handleStopReplay} isPlayingReplay={isPlayingReplay} currentReplayPointId={currentReplayPointId} />
        </section>

        {/* --- Right Sidebar --- */}
        <aside className="replay-sidebar replay-sidebar-right">
           <h4>Sponsor Area</h4>
           {/* *** ADD CHECK: Ensure currentRightAd exists before accessing .type *** */}
           {currentRightAd && currentRightAd.type === 'image' && (
            <a href={currentRightAd.link || '#'} target="_blank" rel="noopener noreferrer">
               <img src={currentRightAd.src} alt={currentRightAd.alt} width="160" height="600" />
            </a>
           )}
           {/* *** ADD CHECK: Ensure currentRightAd exists before accessing .type *** */}
           {currentRightAd && currentRightAd.type === 'text' && (
             <div style={{ border: '1px dashed grey', width: '160px', height: '600px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#eee', padding: '5px', textAlign: 'center' }}>
               {currentRightAd.text}
             </div>
           )}
           {/* Optional: Placeholder if no ad */}
           {!currentRightAd && (
             <div style={{ width: '160px', height: '600px', background: '#ddd' }}></div>
           )}
        </aside>
      </div>
    </div>
  );
}

export default Replay;