// src/components/TennisCourt3D.jsx
import React, { useState, useEffect, useRef } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Plane, Sphere, Line, Cylinder } from '@react-three/drei'; // Ensure Cylinder is imported
import * as THREE from 'three';
import Scoreboard from '../Scoreboard/Scoreboard';

// --- Constants ---
const COURT_LENGTH = 23.77;
const COURT_WIDTH_SINGLES = 8.23;
const NET_HEIGHT = 0.914;
const SERVICE_LINE_FROM_NET = 6.4;
const BASELINE_FROM_NET = COURT_LENGTH / 2;
const TRAJECTORY_MAX_POINTS = 150;
const LINE_WIDTH = 0.05;
const POLE_HEIGHT = 1.07;
const POLE_RADIUS = 0.03;

// --- Environment URLs ---
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// --- Coordinate System Mapping ---
const mapCoords = (simX, simY, simZ) => {
    console.log(`mapCoords Input: simX=${simX}, simY=${simY}, simZ=${simZ}`);
    if (simX === undefined || simY === undefined || simZ === undefined || isNaN(simX) || isNaN(simY) || isNaN(simZ)) {
        console.warn("mapCoords received invalid input, returning default.");
        return new THREE.Vector3(0, 0.1, 0);
    }
    const safeZ = Math.max(simZ, 0.01); // Ensure minimum height
    const mappedPos = new THREE.Vector3(simY, safeZ, simX);
    console.log(`mapCoords Output: x=${mappedPos.x.toFixed(2)}, y=${mappedPos.y.toFixed(2)}, z=${mappedPos.z.toFixed(2)}`);
    return mappedPos;
};

// --- Scene Components ---

// *** FULL DEFINITION for TennisCourtLines ***
function TennisCourtLines() {
    const lineColor = '#FFFFFF'; // White
    // Use a MeshBasicMaterial for lines to ensure visibility regardless of light angle
    const lineMaterial = <meshBasicMaterial color={lineColor} side={THREE.DoubleSide}/>;
    const lineY = 0.005; // Lift lines just slightly above the court surface

    return (
        // Position group slightly above court to avoid z-fighting
        <group position={[0, lineY, 0]}>
            {/* Baseline 1 */}
            <Plane args={[COURT_WIDTH_SINGLES, LINE_WIDTH]} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, BASELINE_FROM_NET]} material={lineMaterial} />
            {/* Baseline 2 */}
            <Plane args={[COURT_WIDTH_SINGLES, LINE_WIDTH]} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, -BASELINE_FROM_NET]} material={lineMaterial} />
            {/* Sideline 1 */}
            <Plane args={[LINE_WIDTH, COURT_LENGTH]} rotation={[-Math.PI / 2, 0, 0]} position={[COURT_WIDTH_SINGLES / 2, 0, 0]} material={lineMaterial} />
            {/* Sideline 2 */}
            <Plane args={[LINE_WIDTH, COURT_LENGTH]} rotation={[-Math.PI / 2, 0, 0]} position={[-COURT_WIDTH_SINGLES / 2, 0, 0]} material={lineMaterial} />
            {/* Service Line 1 */}
            <Plane args={[COURT_WIDTH_SINGLES, LINE_WIDTH]} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, SERVICE_LINE_FROM_NET]} material={lineMaterial} />
             {/* Service Line 2 */}
             <Plane args={[COURT_WIDTH_SINGLES, LINE_WIDTH]} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, -SERVICE_LINE_FROM_NET]} material={lineMaterial} />
            {/* Center Service Line */}
            <Plane args={[LINE_WIDTH, SERVICE_LINE_FROM_NET * 2]} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} material={lineMaterial} />
             {/* Optional Center Mark (Baseline) - Small lines
             <Plane args={[LINE_WIDTH, 0.1]} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, BASELINE_FROM_NET - (0.1/2)]} material={lineMaterial} />
             <Plane args={[LINE_WIDTH, 0.1]} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, -BASELINE_FROM_NET + (0.1/2)]} material={lineMaterial} />
             */}
        </group>
    );
}

// *** FULL DEFINITION for TennisCourt ***
function TennisCourt() {
    const courtColor = '#4A9A4A'; // Greenish court
    const netColor = '#111111';   // Darker net
    const poleColor = '#444444';  // Dark grey poles

    return (
        <group>
            {/* Court Base - Use standard material for lighting effects */}
            <Plane args={[COURT_WIDTH_SINGLES + LINE_WIDTH, COURT_LENGTH + LINE_WIDTH]} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
                <meshStandardMaterial color={courtColor} />
            </Plane>

            {/* Court Lines */}
            <TennisCourtLines />

            {/* Net */}
            <Plane args={[COURT_WIDTH_SINGLES, NET_HEIGHT]} rotation={[0, 0, 0]} position={[0, NET_HEIGHT / 2, 0]}>
                <meshStandardMaterial color={netColor} side={THREE.DoubleSide} transparent opacity={0.7} roughness={0.8}/>
            </Plane>
            {/* Net Top Cord - Use Cylinder */}
             <Cylinder args={[0.01, 0.01, COURT_WIDTH_SINGLES, 8]} position={[0, NET_HEIGHT, 0]} rotation={[0, 0, Math.PI / 2]}>
                <meshStandardMaterial color="#FFFFFF" />
            </Cylinder>

            {/* Net Poles - Use Cylinder */}
            <Cylinder args={[POLE_RADIUS, POLE_RADIUS, POLE_HEIGHT, 12]} position={[COURT_WIDTH_SINGLES / 2 + POLE_RADIUS, POLE_HEIGHT / 2, 0]}>
                 <meshStandardMaterial color={poleColor} />
            </Cylinder>
             <Cylinder args={[POLE_RADIUS, POLE_RADIUS, POLE_HEIGHT, 12]} position={[-COURT_WIDTH_SINGLES / 2 - POLE_RADIUS, POLE_HEIGHT / 2, 0]}>
                 <meshStandardMaterial color={poleColor} />
            </Cylinder>
        </group>
    );
}


// *** BALL COMPONENT - Reverted Debugging Changes ***
function Ball({ position }) {
    console.log("Ball Component Rendered with position:", position); // Keep log for now
    if (!position || !(position instanceof THREE.Vector3) || isNaN(position.x) || isNaN(position.y) || isNaN(position.z) ) {
       console.warn("Invalid position prop passed to Ball component:", position);
       return null;
    }
    // Standard tennis ball size is ~6.7cm diameter -> radius ~0.0335m
    return (
        <Sphere args={[0.035, 16, 16]} position={position}>
            {/* Standard tennis ball yellow/green */}
            <meshStandardMaterial color="#ccff00" roughness={0.6} metalness={0.1} />
        </Sphere>
    );
}

// *** TRAJECTORY COMPONENT - Reverted Debugging Changes ***
function Trajectory({ points }) {
     console.log(`Trajectory Component Rendered with ${points?.length || 0} points.`); // Keep log for now
    if (!points || points.length < 2) return null;
    // Filter points just in case
    const validPoints = points.filter(p => p instanceof THREE.Vector3 && !isNaN(p.x) && !isNaN(p.y) && !isNaN(p.z));
     if (validPoints.length < 2) return null;
    // Standard line width
    return <Line points={validPoints} color="#FFA500" lineWidth={2} />; // Orange color
}


// --- Main Component ---
function TennisCourt3D({ isReplayActive, replayPointId }) {
    const initialBallPos = mapCoords(0, 0, 0.1);
    const [ballPosition, setBallPosition] = useState(initialBallPos);
    const [trajectoryPoints, setTrajectoryPoints] = useState([]);
    const [replayCoords, setReplayCoords] = useState([]);
    const [currentReplayCoordIndex, setCurrentReplayCoordIndex] = useState(0);
    const [replayScoreContext, setReplayScoreContext] = useState(null);
    const replayTimeoutRef = useRef(null);
    const isMounted = useRef(true);

    console.log("TennisCourt3D Render. isReplayActive:", isReplayActive, "replayPointId:", replayPointId);
    console.log("Current ballPosition state:", ballPosition);


    // --- Replay Data Fetching Effect --- (Keep as is)
    useEffect(() => {
        isMounted.current = true;
        console.log("Replay Fetch Effect Triggered. isReplayActive:", isReplayActive, "replayPointId:", replayPointId);

        if (isReplayActive && replayPointId !== null) {
            console.log(`Fetching replay data for point ${replayPointId}`);
            setTrajectoryPoints([]);
            setReplayScoreContext(null);
            const apiUrl = `${API_BASE_URL}/api/tracker/points/${replayPointId}/replay/`;
            fetch(apiUrl)
                .then(res => {
                    if (!res.ok) { return res.text().then(text => { throw new Error(`HTTP error fetching replay! Status: ${res.status}, Body: ${text}`); }); }
                    return res.json();
                })
                .then(data => {
                     console.log("Replay data fetched:", data);
                     if (!isMounted.current) return;
                     if (data.coordinates && data.coordinates.length > 0) {
                        console.log(`First coordinate raw: x=${data.coordinates[0].x}, y=${data.coordinates[0].y}, z=${data.coordinates[0].z}`);
                        setReplayCoords(data.coordinates);
                        setCurrentReplayCoordIndex(0);
                        const firstCoord = data.coordinates[0];
                        const initialMappedPos = mapCoords(firstCoord.x, firstCoord.y, firstCoord.z);
                        console.log("Setting initial replay position to:", initialMappedPos);
                        setBallPosition(initialMappedPos);
                        setTrajectoryPoints([initialMappedPos]);
                        // Ensure your serializer includes these fields with these names or adjust here
                        setReplayScoreContext({
                             team1Points: data.team1_points_at_start ?? '0',
                             team2Points: data.team2_points_at_start ?? '0',
                             team1Games: data.team1_games_at_start ?? 0,
                             team2Games: data.team2_games_at_start ?? 0,
                             currentSet: data.set_number_at_start ?? 1,
                             serverPlayer: data.server_player ?? null,
                         });
                    } else {
                        console.log("No coordinates found to replay for point:", replayPointId);
                        setReplayCoords([]); setReplayScoreContext(null);
                     }
                })
                .catch(error => {
                     if (isMounted.current) {
                          console.error("Error fetching replay data:", error);
                          setReplayCoords([]); setReplayScoreContext(null);
                     }
                 });
        } else {
             console.log("Clearing replay state because isReplayActive is false or replayPointId is null.");
            setReplayCoords([]); setCurrentReplayCoordIndex(0); setReplayScoreContext(null);
            console.log("Resetting ball position to initial state:", initialBallPos);
            setBallPosition(initialBallPos);
            setTrajectoryPoints([]);
        }
        return () => { isMounted.current = false; if (replayTimeoutRef.current) clearTimeout(replayTimeoutRef.current); };
    }, [isReplayActive, replayPointId]);


    // --- Replay Loop Effect --- (Keep as is)
     useEffect(() => {
        console.log("Replay Loop Effect Triggered. Index:", currentReplayCoordIndex, "Total Coords:", replayCoords.length);
        if (!isReplayActive || replayCoords.length === 0 || currentReplayCoordIndex >= replayCoords.length) {
             if (isReplayActive && replayCoords.length > 0 && currentReplayCoordIndex >= replayCoords.length) console.log("Replay loop finished for point:", replayPointId);
            return;
        }
        if (replayTimeoutRef.current) clearTimeout(replayTimeoutRef.current);

        const currentCoord = replayCoords[currentReplayCoordIndex];
        console.log(`Replay Loop: Processing coord index ${currentReplayCoordIndex}:`, currentCoord);
        const nextCoord = replayCoords[currentReplayCoordIndex + 1];
        const newPos = mapCoords(currentCoord.x, currentCoord.y, currentCoord.z);

         if (isMounted.current) {
             console.log(`Replay Loop: Setting ballPosition to: x=${newPos.x.toFixed(2)}, y=${newPos.y.toFixed(2)}, z=${newPos.z.toFixed(2)}`);
            setBallPosition(newPos);
            setTrajectoryPoints(prevPoints => {
                 if (prevPoints.length > 0 && prevPoints[prevPoints.length - 1].equals(newPos)) return prevPoints;
                 const updatedPoints = [...prevPoints, newPos];
                 return updatedPoints.length > TRAJECTORY_MAX_POINTS ? updatedPoints.slice(updatedPoints.length - TRAJECTORY_MAX_POINTS) : updatedPoints;
             });
         }

        if (nextCoord) {
            const delay = nextCoord.relative_time_ms - currentCoord.relative_time_ms;
            console.log(`Replay Loop: Scheduling next update in ${delay}ms`);
            replayTimeoutRef.current = setTimeout(() => {
                 if (isMounted.current && isReplayActive) setCurrentReplayCoordIndex(prevIndex => prevIndex + 1);
            }, delay > 0 ? delay : 5);
        } else { console.log("Reached end of replay coordinates array for point:", replayPointId); }
        return () => { if (replayTimeoutRef.current) clearTimeout(replayTimeoutRef.current); };
    }, [isReplayActive, replayCoords, currentReplayCoordIndex, replayPointId]);

    // --- Determine Scoreboard Props --- (Keep as is)
    const scoreboardProps = replayScoreContext || { team1Points: '-', team2Points: '-', team1Games: '-', team2Games: '-', currentSet: '-', serverPlayer: null };

    return (
         <>
            <Scoreboard {...scoreboardProps} />
            <div style={{ height: '60vh', width: '100%', background: '#ADD8E6', marginBottom: '20px' }}>
                {/* Set clearColor on Canvas for explicit background control */}
                <Canvas clearColor="#ADD8E6" camera={{ position: [0, 12, COURT_LENGTH * 0.8], fov: 55 }}>
                    {/* Lighting and Controls */}
                    <ambientLight intensity={0.7} />
                    {/* Make directional lights brighter */}
                    <directionalLight position={[5, 15, 10]} intensity={1.0} castShadow />
                    <directionalLight position={[-5, 10, -10]} intensity={0.6} />
                    <OrbitControls enablePan={true} enableZoom={true} enableRotate={true}/>

                    {/* Scene Components - Now using full definitions */}
                    <TennisCourt />
                    {replayCoords.length > 0 && <Ball position={ballPosition} />}
                    {replayCoords.length > 0 && <Trajectory points={trajectoryPoints} />}

                    {/* Optional Helpers */}
                    {/* <gridHelper args={[30, 30]} position={[0, -0.001, 0]} /> */}
                    {/* <axesHelper args={[5]} /> */}
                </Canvas>
            </div>
         </>
    );
}

export default TennisCourt3D;