// src/components/TennisCourt3D.jsx
import React, { useState, useEffect, useRef } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Plane, Sphere, Line, Text } from '@react-three/drei';
import * as THREE from 'three';

// --- Constants ---
const COURT_LENGTH = 23.77;
const COURT_WIDTH_SINGLES = 8.23;
const COURT_WIDTH_DOUBLES = 10.97; // For reference if needed
const NET_HEIGHT = 0.914;
const SERVICE_LINE_FROM_NET = 6.4;
const BASELINE_FROM_NET = COURT_LENGTH / 2;
const TRAJECTORY_MAX_POINTS = 150; // Max points in the trajectory line
const LINE_WIDTH = 0.05; // Thickness of court lines
const POLE_HEIGHT = 1.07;
const POLE_RADIUS = 0.03;

// --- Environment URLs ---
// Use || for fallback during development if .env isn't set up yet
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
// *** Use the VITE_WS_BASE_URL variable for WebSockets ***
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';


// --- Coordinate System Mapping ---
const mapCoords = (simX, simY, simZ) => {
    if (simX === undefined || simY === undefined || simZ === undefined) {
        console.warn("mapCoords received undefined input");
        return new THREE.Vector3(0, 0.1, 0); // Default safe position
    }
    // Make sure Z (height) isn't negative if needed for visuals
    const safeZ = Math.max(simZ, 0);
    return new THREE.Vector3(simY, safeZ, simX);
};

// --- Scene Components ---

function TennisCourtLines() {
    const lineColor = '#FFFFFF'; // White
    const lineMaterial = <meshStandardMaterial color={lineColor} />;
    const lineY = 0.01; // Slightly above court surface

    return (
        <group>
            {/* Baseline 1 */}
            <Plane args={[COURT_WIDTH_SINGLES, LINE_WIDTH]} rotation={[-Math.PI / 2, 0, 0]} position={[0, lineY, BASELINE_FROM_NET]} material={lineMaterial} />
            {/* Baseline 2 */}
            <Plane args={[COURT_WIDTH_SINGLES, LINE_WIDTH]} rotation={[-Math.PI / 2, 0, 0]} position={[0, lineY, -BASELINE_FROM_NET]} material={lineMaterial} />
            {/* Sideline 1 */}
            <Plane args={[LINE_WIDTH, COURT_LENGTH]} rotation={[-Math.PI / 2, 0, 0]} position={[COURT_WIDTH_SINGLES / 2, lineY, 0]} material={lineMaterial} />
            {/* Sideline 2 */}
            <Plane args={[LINE_WIDTH, COURT_LENGTH]} rotation={[-Math.PI / 2, 0, 0]} position={[-COURT_WIDTH_SINGLES / 2, lineY, 0]} material={lineMaterial} />
            {/* Service Line 1 */}
            <Plane args={[COURT_WIDTH_SINGLES, LINE_WIDTH]} rotation={[-Math.PI / 2, 0, 0]} position={[0, lineY, SERVICE_LINE_FROM_NET]} material={lineMaterial} />
             {/* Service Line 2 */}
             <Plane args={[COURT_WIDTH_SINGLES, LINE_WIDTH]} rotation={[-Math.PI / 2, 0, 0]} position={[0, lineY, -SERVICE_LINE_FROM_NET]} material={lineMaterial} />
            {/* Center Service Line */}
            <Plane args={[LINE_WIDTH, SERVICE_LINE_FROM_NET * 2]} rotation={[-Math.PI / 2, 0, 0]} position={[0, lineY, 0]} material={lineMaterial} />
             {/* Net Line (under the net visually) */}
             <Plane args={[COURT_WIDTH_SINGLES, LINE_WIDTH]} rotation={[-Math.PI / 2, 0, 0]} position={[0, lineY, 0]} material={lineMaterial} />
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
            <TennisCourtLines /> {/* Uses the component defined above */}

            {/* Net */}
            <Plane args={[COURT_WIDTH_SINGLES, NET_HEIGHT]} rotation={[0, 0, 0]} position={[0, NET_HEIGHT / 2, 0]}>
                <meshStandardMaterial color={netColor} side={THREE.DoubleSide} transparent opacity={0.6} />
            </Plane>
            {/* Net Top Cord */}
            <mesh position={[0, NET_HEIGHT, 0]}>
                <cylinderGeometry args={[0.01, 0.01, COURT_WIDTH_SINGLES, 8]} />
                <meshStandardMaterial color="#FFFFFF" />
            </mesh>

            {/* Net Poles (simple cylinders) */}
            <mesh position={[COURT_WIDTH_SINGLES / 2 + 0.1, POLE_HEIGHT / 2, 0]}>
                 <cylinderGeometry args={[POLE_RADIUS, POLE_RADIUS, POLE_HEIGHT, 12]} />
                 <meshStandardMaterial color={poleColor} />
            </mesh>
             <mesh position={[-COURT_WIDTH_SINGLES / 2 - 0.1, POLE_HEIGHT / 2, 0]}>
                 <cylinderGeometry args={[POLE_RADIUS, POLE_RADIUS, POLE_HEIGHT, 12]} />
                 <meshStandardMaterial color={poleColor} />
            </mesh>
        </group>
    );
}

function Ball({ position }) {
    // Ensure position is valid before rendering
    if (!position || !(position instanceof THREE.Vector3)) {
       console.warn("Invalid ball position passed to Ball component");
       return null; // Don't render if position is invalid
    }
    return (
        <Sphere args={[0.065, 16, 16]} position={position}>
            <meshStandardMaterial color="yellow" />
        </Sphere>
    );
}

function Trajectory({ points }) {
    if (!points || points.length < 2) {
        return null;
    }
    // Ensure points are valid THREE.Vector3 instances if needed
    const validPoints = points.filter(p => p instanceof THREE.Vector3);
     if (validPoints.length < 2) return null;
    return <Line points={validPoints} color="orange" lineWidth={2} />;
}

// --- Main Component ---
// Renamed props for clarity
function TennisCourt3D({ isReplayActive, replayPointId }) {
    const [ballPosition, setBallPosition] = useState(mapCoords(0, 0, 0.1));
    const [trajectoryPoints, setTrajectoryPoints] = useState([]);
    const [replayCoords, setReplayCoords] = useState([]);
    const [currentReplayCoordIndex, setCurrentReplayCoordIndex] = useState(0);
    const ws = useRef(null);
    const replayTimeoutRef = useRef(null);
    const isMounted = useRef(true); // Track component mount state

    // --- WebSocket Connection Effect ---
    useEffect(() => {
        // Set mount status
        isMounted.current = true;

        // *** Construct WebSocket URL from environment variable ***
        const wsUrl = `${WS_BASE_URL}/ws/tracker/`;
        console.log(`Connecting WebSocket to ${wsUrl}`);

        // Avoid creating multiple connections if one is already open/connecting
        // Close existing cleanly before creating a new one
        if (ws.current) {
             console.log(`Closing existing WebSocket (State: ${ws.current.readyState}) before reconnecting.`);
             ws.current.close(1000, "Component re-initializing"); // Close cleanly
        }

        // Don't try to connect if we are currently replaying
        if (isReplayActive) {
             console.log("Replay active, skipping WebSocket connection setup.");
             return; // Exit effect early
        }


        // Create new WebSocket connection
        ws.current = new WebSocket(wsUrl);

        ws.current.onopen = () => {
            if (!isMounted.current) return; // Check if component unmounted before open fires
            console.log("WebSocket Connected to", wsUrl);
        };
        ws.current.onclose = (event) => {
            // Don't log if closed intentionally by cleanup
            if (event.code !== 1000) {
                 console.log("WebSocket Disconnected:", event.reason, "Code:", event.code);
            }
        };
        ws.current.onerror = (error) => {
            console.error("WebSocket Error:", error);
        };

        ws.current.onmessage = (event) => {
             // Check mount status and if replay is active inside the handler too
            if (isReplayActive || !isMounted.current) return;

            try {
                const message = JSON.parse(event.data);
                if (message.type === 'coords' && message.payload) {
                    const { x, y, z } = message.payload;
                    const newPosition = mapCoords(x, y, z);
                    // Check mount status before state updates
                    if (isMounted.current) {
                         setBallPosition(newPosition);
                         setTrajectoryPoints(prevPoints => {
                             const updatedPoints = [...prevPoints, newPosition];
                             return updatedPoints.length > TRAJECTORY_MAX_POINTS
                                 ? updatedPoints.slice(updatedPoints.length - TRAJECTORY_MAX_POINTS)
                                 : updatedPoints;
                         });
                    }
                } else if (message.type === 'out_signal' || message.type === 'clock_stop') {
                    // Clear trajectory on point end signals
                    if (isMounted.current) {
                         setTrajectoryPoints([]);
                    }
                }
                // Add handling for other message types if needed
            } catch (error) {
                console.error("Failed to parse WebSocket message:", event.data, error);
            }
        };

        // --- Cleanup function ---
        return () => {
            isMounted.current = false; // Mark as unmounted
            if (replayTimeoutRef.current) {
                clearTimeout(replayTimeoutRef.current); // Clear any pending replay timeouts
            }
            if (ws.current) {
                console.log("Closing WebSocket connection on component unmount/effect cleanup.");
                // Don't set onclose/onerror to null here, just close
                ws.current.close(1000, "Component unmounting"); // 1000 is normal closure
                ws.current = null; // Help garbage collection
            }
        };
    // Re-run this effect if the replay state changes (to connect/disconnect WebSocket)
    }, [isReplayActive]); // Dependency array includes isReplayActive


    // --- Replay Data Fetching Effect ---
    useEffect(() => {
        if (isReplayActive && replayPointId !== null) {
             if (!isMounted.current) return; // Check mount status
            console.log(`Fetching replay data for point ${replayPointId}`);
            setTrajectoryPoints([]); // Clear live trajectory for replay
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
                     if (!isMounted.current) return; // Check mount status again after async fetch
                     if (data.coordinates && data.coordinates.length > 0) {
                        setReplayCoords(data.coordinates);
                        setCurrentReplayCoordIndex(0); // Start from the beginning
                        // Set initial position for the replay
                        const firstCoord = data.coordinates[0];
                        setBallPosition(mapCoords(firstCoord.x, firstCoord.y, firstCoord.z));
                        // Start trajectory with the first point
                        setTrajectoryPoints([mapCoords(firstCoord.x, firstCoord.y, firstCoord.z)]);
                    } else {
                        console.log("No coordinates found to replay for point:", replayPointId);
                        setReplayCoords([]); // Clear coords if none found
                    }
                })
                .catch(error => {
                    if (isMounted.current) {
                         console.error("Error fetching replay data:", error);
                         setReplayCoords([]); // Clear coords on error
                    }
                });
        } else if (!isReplayActive) {
            // If replay stopped, clear replay data
            setReplayCoords([]);
            setCurrentReplayCoordIndex(0);
            // Optionally clear the last replay trajectory or leave it
             // setTrajectoryPoints([]);
        }
    }, [isReplayActive, replayPointId]); // Dependencies for fetching


    // --- Replay Loop Effect ---
     useEffect(() => {
        // Conditions to run the loop
        if (!isPlayingReplay || replayCoords.length === 0 || currentReplayCoordIndex >= replayCoords.length) {
            // If replay finished naturally (index out of bounds)
            if (isPlayingReplay && replayCoords.length > 0 && currentReplayCoordIndex >= replayCoords.length) {
                console.log("Replay loop finished for point:", replayPointId);
                // Optionally notify parent component that replay is done, e.g., via a callback prop
                // onStopReplay?.(); // Call parent's stop function if provided
            }
            return; // Don't run loop if not playing, no coords, or index out of bounds
        }

        // Clear previous timeout just in case
        if (replayTimeoutRef.current) {
             clearTimeout(replayTimeoutRef.current);
        }

        const currentCoord = replayCoords[currentReplayCoordIndex];
        const nextCoord = replayCoords[currentReplayCoordIndex + 1];

        // Update visualization
        const newPos = mapCoords(currentCoord.x, currentCoord.y, currentCoord.z);
        // Check mount status before setting state
         if (isMounted.current) {
            setBallPosition(newPos);
            // Add point to trajectory, prevent duplicates if delay is 0
            setTrajectoryPoints(prevPoints => {
                 if (prevPoints.length > 0 && prevPoints[prevPoints.length - 1].equals(newPos)) {
                     return prevPoints; // Avoid adding identical consecutive points
                 }
                 const updatedPoints = [...prevPoints, newPos];
                 // Limit trajectory length
                 return updatedPoints.length > TRAJECTORY_MAX_POINTS
                    ? updatedPoints.slice(updatedPoints.length - TRAJECTORY_MAX_POINTS)
                    : updatedPoints;
             });
         }

        // Schedule the next step
        if (nextCoord) {
            const delay = nextCoord.relative_time_ms - currentCoord.relative_time_ms;
            replayTimeoutRef.current = setTimeout(() => {
                 // Check mount status before updating index
                 if (isMounted.current && isPlayingReplay) { // Double check isPlayingReplay hasn't changed
                    setCurrentReplayCoordIndex(prevIndex => prevIndex + 1);
                 }
            }, delay > 0 ? delay : 5); // Use a minimum delay (e.g., 5ms) if coords have same timestamp
        } else {
            // This was the last coordinate, the condition at the start will handle completion
             console.log("Reached end of replay coordinates array for point:", replayPointId);
        }

        // Cleanup timeout on effect cleanup or re-run
        return () => {
            if (replayTimeoutRef.current) {
                clearTimeout(replayTimeoutRef.current);
            }
        };
    // Dependencies: run loop step when index changes or replay starts/coords arrive
    }, [isPlayingReplay, replayCoords, currentReplayCoordIndex, replayPointId]);


    return (
         <div style={{ height: '60vh', width: '100%', background: '#ADD8E6', marginBottom: '20px' }}>
             <Canvas camera={{ position: [0, 12, COURT_LENGTH * 0.8], fov: 55 }}>
                <ambientLight intensity={0.7} />
                <directionalLight position={[5, 15, 10]} intensity={0.8} castShadow />
                <directionalLight position={[-5, 10, -10]} intensity={0.4} />
                <OrbitControls />
                {/* Scene components */}
                <TennisCourt />
                <Ball position={ballPosition} />
                <Trajectory points={trajectoryPoints} />
            </Canvas>
        </div>
    );
}

export default TennisCourt3D;// src/components/TennisCourt3D.jsx
import React, { useState, useEffect, useRef } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Plane, Sphere, Line, Text } from '@react-three/drei';
import * as THREE from 'three';

// --- Constants ---
const COURT_LENGTH = 23.77;
const COURT_WIDTH_SINGLES = 8.23;
const COURT_WIDTH_DOUBLES = 10.97; // For reference if needed
const NET_HEIGHT = 0.914;
const SERVICE_LINE_FROM_NET = 6.4;
const BASELINE_FROM_NET = COURT_LENGTH / 2;
const TRAJECTORY_MAX_POINTS = 150; // Max points in the trajectory line
const LINE_WIDTH = 0.05; // Thickness of court lines
const POLE_HEIGHT = 1.07;
const POLE_RADIUS = 0.03;

// --- Environment URLs ---
// Use || for fallback during development if .env isn't set up yet
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';


// --- Coordinate System Mapping ---
const mapCoords = (simX, simY, simZ) => {
    if (simX === undefined || simY === undefined || simZ === undefined) {
        console.warn("mapCoords received undefined input");
        return new THREE.Vector3(0, 0.1, 0); // Default safe position
    }
    return new THREE.Vector3(simY, simZ, simX);
};

// --- Scene Components --- <<<< ****** ADDED THESE DEFINITIONS BACK ******

function TennisCourtLines() {
    const lineColor = '#FFFFFF'; // White
    const lineMaterial = <meshStandardMaterial color={lineColor} />;
    const lineY = 0.01; // Slightly above court surface

    return (
        <group>
            {/* Baseline 1 */}
            <Plane args={[COURT_WIDTH_SINGLES, LINE_WIDTH]} rotation={[-Math.PI / 2, 0, 0]} position={[0, lineY, BASELINE_FROM_NET]} material={lineMaterial} />
            {/* Baseline 2 */}
            <Plane args={[COURT_WIDTH_SINGLES, LINE_WIDTH]} rotation={[-Math.PI / 2, 0, 0]} position={[0, lineY, -BASELINE_FROM_NET]} material={lineMaterial} />
            {/* Sideline 1 */}
            <Plane args={[LINE_WIDTH, COURT_LENGTH]} rotation={[-Math.PI / 2, 0, 0]} position={[COURT_WIDTH_SINGLES / 2, lineY, 0]} material={lineMaterial} />
            {/* Sideline 2 */}
            <Plane args={[LINE_WIDTH, COURT_LENGTH]} rotation={[-Math.PI / 2, 0, 0]} position={[-COURT_WIDTH_SINGLES / 2, lineY, 0]} material={lineMaterial} />
            {/* Service Line 1 */}
            <Plane args={[COURT_WIDTH_SINGLES, LINE_WIDTH]} rotation={[-Math.PI / 2, 0, 0]} position={[0, lineY, SERVICE_LINE_FROM_NET]} material={lineMaterial} />
             {/* Service Line 2 */}
             <Plane args={[COURT_WIDTH_SINGLES, LINE_WIDTH]} rotation={[-Math.PI / 2, 0, 0]} position={[0, lineY, -SERVICE_LINE_FROM_NET]} material={lineMaterial} />
            {/* Center Service Line */}
            <Plane args={[LINE_WIDTH, SERVICE_LINE_FROM_NET * 2]} rotation={[-Math.PI / 2, 0, 0]} position={[0, lineY, 0]} material={lineMaterial} />
             {/* Net Line (under the net visually) */}
             <Plane args={[COURT_WIDTH_SINGLES, LINE_WIDTH]} rotation={[-Math.PI / 2, 0, 0]} position={[0, lineY, 0]} material={lineMaterial} />
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
            <TennisCourtLines /> {/* Uses the component defined above */}

            {/* Net */}
            <Plane args={[COURT_WIDTH_SINGLES, NET_HEIGHT]} rotation={[0, 0, 0]} position={[0, NET_HEIGHT / 2, 0]}>
                <meshStandardMaterial color={netColor} side={THREE.DoubleSide} transparent opacity={0.6} />
            </Plane>
            {/* Net Top Cord */}
            <mesh position={[0, NET_HEIGHT, 0]}>
                <cylinderGeometry args={[0.01, 0.01, COURT_WIDTH_SINGLES, 8]} />
                <meshStandardMaterial color="#FFFFFF" />
            </mesh>

            {/* Net Poles (simple cylinders) */}
            <mesh position={[COURT_WIDTH_SINGLES / 2 + 0.1, POLE_HEIGHT / 2, 0]}>
                 <cylinderGeometry args={[POLE_RADIUS, POLE_RADIUS, POLE_HEIGHT, 12]} />
                 <meshStandardMaterial color={poleColor} />
            </mesh>
             <mesh position={[-COURT_WIDTH_SINGLES / 2 - 0.1, POLE_HEIGHT / 2, 0]}>
                 <cylinderGeometry args={[POLE_RADIUS, POLE_RADIUS, POLE_HEIGHT, 12]} />
                 <meshStandardMaterial color={poleColor} />
            </mesh>
        </group>
    );
}

function Ball({ position }) {
    // Ensure position is valid before rendering
    if (!position || !(position instanceof THREE.Vector3)) {
       console.warn("Invalid ball position passed to Ball component");
       return null; // Don't render if position is invalid
    }
    return (
        <Sphere args={[0.065, 16, 16]} position={position}>
            <meshStandardMaterial color="yellow" />
        </Sphere>
    );
}

function Trajectory({ points }) {
    if (!points || points.length < 2) {
        return null;
    }
    // Ensure points are valid THREE.Vector3 instances if needed
    const validPoints = points.filter(p => p instanceof THREE.Vector3);
     if (validPoints.length < 2) return null;
    return <Line points={validPoints} color="orange" lineWidth={2} />;
}

// --- Main Component ---
function TennisCourt3D({ isPlayingReplay, pointIdToReplay }) {
    const [ballPosition, setBallPosition] = useState(mapCoords(0, 0, 0.1));
    const [trajectoryPoints, setTrajectoryPoints] = useState([]);
    const [replayCoords, setReplayCoords] = useState([]);
    const [currentReplayCoordIndex, setCurrentReplayCoordIndex] = useState(0);
    const ws = useRef(null);
    const replayTimeoutRef = useRef(null);
    const isMounted = useRef(true);

    // --- WebSocket Connection Effect ---
    useEffect(() => {
        isMounted.current = true;
        const wsUrl = `${WS_BASE_URL}/ws/tracker/`;
        console.log(`Connecting WebSocket to ${wsUrl}`);

        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
             console.log("WebSocket already open.");
        }
        if (ws.current) {
            ws.current.close();
        }

        ws.current = new WebSocket(wsUrl);
        ws.current.onopen = () => console.log("WebSocket Connected to", wsUrl);
        ws.current.onclose = (event) => console.log("WebSocket Disconnected:", event.reason, "Code:", event.code);
        ws.current.onerror = (error) => console.error("WebSocket Error:", error);

        ws.current.onmessage = (event) => {
            if (isPlayingReplay || !isMounted.current) return;

            try {
                const message = JSON.parse(event.data);
                if (message.type === 'coords' && message.payload) {
                    const { x, y, z } = message.payload;
                    const newPosition = mapCoords(x, y, z);
                    setBallPosition(newPosition);
                    setTrajectoryPoints(prevPoints => {
                        const updatedPoints = [...prevPoints, newPosition];
                        return updatedPoints.length > TRAJECTORY_MAX_POINTS
                            ? updatedPoints.slice(updatedPoints.length - TRAJECTORY_MAX_POINTS)
                            : updatedPoints;
                    });
                } else if (message.type === 'out_signal' || message.type === 'clock_stop') {
                    setTrajectoryPoints([]);
                }
            } catch (error) {
                console.error("Failed to parse WebSocket message:", event.data, error);
            }
        };

        return () => {
            isMounted.current = false;
            if (ws.current) {
                console.log("Closing WebSocket connection on cleanup");
                ws.current.close();
            }
            if (replayTimeoutRef.current) {
                clearTimeout(replayTimeoutRef.current);
            }
        };
    }, [isPlayingReplay]);

    // --- Replay Data Fetching Effect ---
    useEffect(() => {
        if (isPlayingReplay && pointIdToReplay !== null) {
            console.log(`Fetching replay data for point ${pointIdToReplay}`);
            setTrajectoryPoints([]);
            const apiUrl = `${API_BASE_URL}/api/tracker/points/${pointIdToReplay}/replay/`;
            console.log(`Fetching from: ${apiUrl}`)

            fetch(apiUrl)
                .then(res => {
                    if (!res.ok) {
                        return res.text().then(text => {
                           throw new Error(`HTTP error! Status: ${res.status}, Body: ${text}`);
                        });
                    }
                    return res.json();
                })
                .then(data => {
                     if (data.coordinates && data.coordinates.length > 0) {
                         if (!isMounted.current) return;
                        setReplayCoords(data.coordinates);
                        setCurrentReplayCoordIndex(0);
                        const firstCoord = data.coordinates[0];
                        setBallPosition(mapCoords(firstCoord.x, firstCoord.y, firstCoord.z));
                        setTrajectoryPoints([mapCoords(firstCoord.x, firstCoord.y, firstCoord.z)]);
                    } else {
                        console.log("No coordinates found for point:", pointIdToReplay);
                        setReplayCoords([]);
                    }
                })
                .catch(error => {
                    console.error("Error fetching replay data:", error);
                    setReplayCoords([]);
                });
        } else {
            setReplayCoords([]);
            setCurrentReplayCoordIndex(0);
        }
    }, [isPlayingReplay, pointIdToReplay]);

    // --- Replay Loop Effect ---
     useEffect(() => {
        if (!isPlayingReplay || replayCoords.length === 0 || currentReplayCoordIndex >= replayCoords.length) {
            return;
        }
        if (replayTimeoutRef.current) {
             clearTimeout(replayTimeoutRef.current);
        }
        const currentCoord = replayCoords[currentReplayCoordIndex];
        const nextCoord = replayCoords[currentReplayCoordIndex + 1];
        const newPos = mapCoords(currentCoord.x, currentCoord.y, currentCoord.z);
        setBallPosition(newPos);
        setTrajectoryPoints(prevPoints => {
            if (prevPoints.length > 0 && prevPoints[prevPoints.length - 1].equals(newPos)) {
                return prevPoints;
            }
            const updatedPoints = [...prevPoints, newPos];
            return updatedPoints.length > TRAJECTORY_MAX_POINTS
                ? updatedPoints.slice(updatedPoints.length - TRAJECTORY_MAX_POINTS)
                : updatedPoints;
        });
        if (nextCoord) {
            const delay = nextCoord.relative_time_ms - currentCoord.relative_time_ms;
            replayTimeoutRef.current = setTimeout(() => {
                 if (!isMounted.current) return;
                setCurrentReplayCoordIndex(prevIndex => prevIndex + 1);
            }, delay > 0 ? delay : 5);
        } else {
             console.log("Replay loop finished for point:", pointIdToReplay);
             // NOTE: Consider calling the onStopReplay callback here or letting the parent handle it
             // based on currentReplayCoordIndex >= replayCoords.length
        }
        return () => {
            if (replayTimeoutRef.current) {
                clearTimeout(replayTimeoutRef.current);
            }
        };
    }, [isPlayingReplay, replayCoords, currentReplayCoordIndex, pointIdToReplay]); // Added pointIdToReplay dependency


    return (
         <div style={{ height: '60vh', width: '100%', background: '#ADD8E6', marginBottom: '20px' }}>
             <Canvas camera={{ position: [0, 12, COURT_LENGTH * 0.8], fov: 55 }}>
                <ambientLight intensity={0.7} />
                <directionalLight position={[5, 15, 10]} intensity={0.8} castShadow />
                <directionalLight position={[-5, 10, -10]} intensity={0.4} />
                <OrbitControls />
                {/* Now these components are defined above */}
                <TennisCourt />
                <Ball position={ballPosition} />
                <Trajectory points={trajectoryPoints} />
            </Canvas>
        </div>
    );
}

export default TennisCourt3D;