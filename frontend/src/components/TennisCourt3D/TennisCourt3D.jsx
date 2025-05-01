// src/components/TennisCourt3D.jsx
import React, { useState, useEffect, useRef } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Plane, Sphere, Line } from '@react-three/drei'; // Ensure all needed imports are here
import * as THREE from 'three';
import Scoreboard from '../Scoreboard/Scoreboard'; // Keep scoreboard for replay context

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
    if (simX === undefined || simY === undefined || simZ === undefined) {
        console.warn("mapCoords received undefined input");
        return new THREE.Vector3(0, 0.1, 0);
    }
    const safeZ = Math.max(simZ, 0);
    return new THREE.Vector3(simY, safeZ, simX);
};

// --- Scene Components --- <<< *** RESTORED DEFINITIONS BELOW ***

function TennisCourtLines() {
    const lineColor = '#FFFFFF'; // White
    const lineMaterial = <meshStandardMaterial color={lineColor} side={THREE.DoubleSide}/>; // Added DoubleSide for thin planes
    const lineY = 0.01; // Slightly above court surface

    return (
        <group position={[0, lineY, 0]}> {/* Apply Y offset to group */}
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
             {/* Net Line (optional, usually covered by net visual) */}
             {/* <Plane args={[COURT_WIDTH_SINGLES, LINE_WIDTH]} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} material={lineMaterial} /> */}
        </group>
    );
}

function TennisCourt() {
    const courtColor = '#4A9A4A'; // Greenish
    const netColor = '#222222';
    const poleColor = '#555555';

    return (
        <group>
            {/* Court Base */}
            <Plane args={[COURT_WIDTH_SINGLES, COURT_LENGTH]} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
                <meshStandardMaterial color={courtColor} />
            </Plane>

            {/* Court Lines */}
            <TennisCourtLines /> {/* Render the lines */}

            {/* Net */}
            <Plane args={[COURT_WIDTH_SINGLES, NET_HEIGHT]} rotation={[0, 0, 0]} position={[0, NET_HEIGHT / 2, 0]}>
                {/* Use DoubleSide for the net plane */}
                <meshStandardMaterial color={netColor} side={THREE.DoubleSide} transparent opacity={0.6} />
            </Plane>
            {/* Net Top Cord */}
             <mesh position={[0, NET_HEIGHT, 0]} rotation={[0, 0, Math.PI / 2]}> {/* Rotate cylinder to be horizontal */}
                <cylinderGeometry args={[0.01, 0.01, COURT_WIDTH_SINGLES, 8]} />
                <meshStandardMaterial color="#FFFFFF" />
            </mesh>

            {/* Net Poles */}
            <mesh position={[COURT_WIDTH_SINGLES / 2 + POLE_RADIUS, POLE_HEIGHT / 2, 0]}>
                 <cylinderGeometry args={[POLE_RADIUS, POLE_RADIUS, POLE_HEIGHT, 12]} />
                 <meshStandardMaterial color={poleColor} />
            </mesh>
             <mesh position={[-COURT_WIDTH_SINGLES / 2 - POLE_RADIUS, POLE_HEIGHT / 2, 0]}>
                 <cylinderGeometry args={[POLE_RADIUS, POLE_RADIUS, POLE_HEIGHT, 12]} />
                 <meshStandardMaterial color={poleColor} />
            </mesh>
        </group>
    );
}

function Ball({ position }) {
    // Ensure position is a valid Vector3 before rendering
    if (!position || !(position instanceof THREE.Vector3)) {
       // console.warn("Invalid ball position passed to Ball component"); // Optional: reduce console noise
       return null;
    }
    return (
        // Make ball slightly larger maybe? 0.0325 radius * 2 = ~6.5cm diameter
        <Sphere args={[0.035, 16, 16]} position={position}>
            <meshStandardMaterial color="#ccff00" /> {/* Brighter yellow/green */}
        </Sphere>
    );
}

function Trajectory({ points }) {
    // Need at least 2 points to draw a line
    if (!points || points.length < 2) {
        return null;
    }
    // Filter points to ensure they are valid THREE.Vector3 instances
    const validPoints = points.filter(p => p instanceof THREE.Vector3);
     if (validPoints.length < 2) return null; // Still need 2 valid points

    // Use Line from drei which handles buffer geometry creation
    return <Line points={validPoints} color="orange" lineWidth={2} />;
}


// --- Main Component ---
function TennisCourt3D({ isReplayActive, replayPointId }) {
    const [ballPosition, setBallPosition] = useState(mapCoords(0, 0, 0.1));
    const [trajectoryPoints, setTrajectoryPoints] = useState([]);
    const [replayCoords, setReplayCoords] = useState([]);
    const [currentReplayCoordIndex, setCurrentReplayCoordIndex] = useState(0);
    const [replayScoreContext, setReplayScoreContext] = useState(null);
    const replayTimeoutRef = useRef(null);
    const isMounted = useRef(true);

    // --- Replay Data Fetching Effect --- (Keep as is)
    useEffect(() => {
        isMounted.current = true;
        if (isReplayActive && replayPointId !== null) {
            console.log(`Fetching replay data for point ${replayPointId}`);
            setTrajectoryPoints([]);
            setReplayScoreContext(null);
            const apiUrl = `${API_BASE_URL}/api/tracker/points/${replayPointId}/replay/`;
            console.log(`Fetching replay from: ${apiUrl}`)
            fetch(apiUrl)
                .then(res => {
                    if (!res.ok) {
                         return res.text().then(text => {
                            throw new Error(`HTTP error fetching replay! Status: ${res.status}, Body: ${text}`);
                         });
                    }
                    return res.json();
                })
                .then(data => {
                     if (!isMounted.current) return;
                     if (data.coordinates && data.coordinates.length > 0) {
                        setReplayCoords(data.coordinates);
                        setCurrentReplayCoordIndex(0);
                        const firstCoord = data.coordinates[0];
                        setBallPosition(mapCoords(firstCoord.x, firstCoord.y, firstCoord.z));
                        setTrajectoryPoints([mapCoords(firstCoord.x, firstCoord.y, firstCoord.z)]);
                        setReplayScoreContext({
                            team1Points: data.team1_score_at_start || '0',
                            team2Points: data.team2_score_at_start || '0',
                            team1Games: data.team1_games_at_start || 0,
                            team2Games: data.team2_games_at_start || 0,
                            currentSet: data.set_number_at_start || 1,
                            serverPlayer: data.server_player || null,
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
            setReplayCoords([]); setCurrentReplayCoordIndex(0); setReplayScoreContext(null);
            setBallPosition(mapCoords(0, 0, 0.1)); setTrajectoryPoints([]);
        }
        return () => {
            isMounted.current = false;
            if (replayTimeoutRef.current) clearTimeout(replayTimeoutRef.current);
        };
    }, [isReplayActive, replayPointId]);

    // --- Replay Loop Effect --- (Keep as is)
     useEffect(() => {
        if (!isReplayActive || replayCoords.length === 0 || currentReplayCoordIndex >= replayCoords.length) {
            if (isReplayActive && replayCoords.length > 0 && currentReplayCoordIndex >= replayCoords.length) {
                 console.log("Replay loop finished for point:", replayPointId);
            } return;
        }
        if (replayTimeoutRef.current) clearTimeout(replayTimeoutRef.current);
        const currentCoord = replayCoords[currentReplayCoordIndex];
        const nextCoord = replayCoords[currentReplayCoordIndex + 1];
        const newPos = mapCoords(currentCoord.x, currentCoord.y, currentCoord.z);
         if (isMounted.current) {
            setBallPosition(newPos);
            setTrajectoryPoints(prevPoints => {
                 if (prevPoints.length > 0 && prevPoints[prevPoints.length - 1].equals(newPos)) return prevPoints;
                 const updatedPoints = [...prevPoints, newPos];
                 return updatedPoints.length > TRAJECTORY_MAX_POINTS
                    ? updatedPoints.slice(updatedPoints.length - TRAJECTORY_MAX_POINTS) : updatedPoints;
             });
         }
        if (nextCoord) {
            const delay = nextCoord.relative_time_ms - currentCoord.relative_time_ms;
            replayTimeoutRef.current = setTimeout(() => {
                 if (isMounted.current && isReplayActive) {
                    setCurrentReplayCoordIndex(prevIndex => prevIndex + 1);
                 }
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
                <Canvas camera={{ position: [0, 12, COURT_LENGTH * 0.8], fov: 55 }}>
                    {/* Lighting and Controls */}
                    <ambientLight intensity={0.7} />
                    <directionalLight position={[5, 15, 10]} intensity={0.8} castShadow />
                    <directionalLight position={[-5, 10, -10]} intensity={0.4} />
                    <OrbitControls enablePan={true} enableZoom={true} enableRotate={true}/> {/* Ensure controls are enabled */}

                    {/* Scene Components */}
                    <TennisCourt />
                    {/* Conditionally render ball/trajectory only when replay has data */}
                    {replayCoords.length > 0 && <Ball position={ballPosition} />}
                    {replayCoords.length > 0 && <Trajectory points={trajectoryPoints} />}

                    {/* Optional: Grid Helper for debugging positions */}
                     {/* <gridHelper args={[COURT_WIDTH_DOUBLES, 10, COURT_LENGTH, 20]} position={[0, 0.001, 0]} /> */}
                     {/* <axesHelper args={[5]} /> */}
                </Canvas>
            </div>
         </>
    );
}

export default TennisCourt3D;