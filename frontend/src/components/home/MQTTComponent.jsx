import React, { useEffect, useState, useRef } from "react";
import mqtt from "mqtt";

const MQTTComponent = () => {
  const mqttClientRef = useRef(null);

  // MQTT state
  const [liveX, setLiveX] = useState("");
  const [liveY, setLiveY] = useState("");
  const [liveZ, setLiveZ] = useState("");
  const [liveCentroid, setLiveCentroid] = useState("");
  const [liveTeam1Pts, setLiveTeam1Pts] = useState("");
  const [liveTeam1Sets, setLiveTeam1Sets] = useState("");
  const [liveTeam2Pts, setLiveTeam2Pts] = useState("");
  const [liveTeam2Sets, setLiveTeam2Sets] = useState("");
  const [liveTeam1Games, setLiveTeam1Games] = useState("");
  const [liveTeam2Games, setLiveTeam2Games] = useState("");

  // Default input values
  const defaultX = "0";
  const defaultY = "0";
  const defaultZ = "0";
  const defaultTeam1Pts = "0";
  const defaultTeam1Sets = "0";
  const defaultTeam2Pts = "0";
  const defaultTeam2Sets = "0";
  const defaultTeam1Games = "0";
  const defaultTeam2Games = "0";

  const [xInput, setXInput] = useState(defaultX);
  const [yInput, setYInput] = useState(defaultY);
  const [zInput, setZInput] = useState(defaultZ);
  const [team1PtsInput, setteam1PtsInput] = useState(defaultTeam1Pts);
  const [team1SetsInput, setteam1SetsInput] = useState(defaultTeam1Sets);
  const [team2PtsInput, setteam2PtsInput] = useState(defaultTeam2Pts);
  const [team2SetsInput, setteam2SetsInput] = useState(defaultTeam2Sets);
  const [team1GamesInput, setTeam1GamesInput] = useState(defaultTeam1Games);
  const [team2GamesInput, setTeam2GamesInput] = useState(defaultTeam2Games);

  useEffect(() => {
    const mqttClient = mqtt.connect("ws://192.168.1.4:8885");
    mqttClientRef.current = mqttClient;

    mqttClient.on("connect", () => {
      mqttClient.subscribe([
        "Ball/xCoordinate",
        "Ball/yCoordinate",
        "Ball/zCoordinate",
        "Ball/centroid",
        "Team1/points",
        "Team1/sets",
        "Team1/games",
        "Team2/points",
        "Team2/sets",
        "Team2/games",
      ]);
    });

    mqttClient.on("message", (topic, payload) => {
      const message = payload.toString();
      switch (topic) {
        case "Ball/xCoordinate":
          setLiveX(message);
          break;
        case "Ball/yCoordinate":
          setLiveY(message);
          break;
        case "Ball/zCoordinate":
          setLiveZ(message);
          break;
        case "Ball/centroid":
          setLiveCentroid(message);
          break;
        case "Team1/points":
          setLiveTeam1Pts(message);
          break;
        case "Team1/sets":
          setLiveTeam1Sets(message);
          break;
        case "Team1/games":
          setLiveTeam1Games(message);
          break;
        case "Team2/points":
          setLiveTeam2Pts(message);
          break;
        case "Team2/sets":
          setLiveTeam2Sets(message);
          break;
        case "Team2/games":
          setLiveTeam2Games(message);
          break;
        default:
          break;
      }
    });

    return () => mqttClient.end();
  }, []);

  const handlePublish = () => {
    const client = mqttClientRef.current;
    if (client) {
      client.publish("Ball/xCoordinate", xInput);
      client.publish("Ball/yCoordinate", yInput);
      client.publish("Ball/zCoordinate", zInput);
      client.publish("Ball/centroid", "0");
      client.publish("Team1/points", team1PtsInput);
      client.publish("Team1/sets", team1SetsInput);
      client.publish("Team1/games", team1GamesInput);
      client.publish("Team2/points", team2PtsInput);
      client.publish("Team2/sets", team2SetsInput);
      client.publish("Team2/games", team2GamesInput);
    }
  };

  const handleClearInputs = () => {
    setXInput(defaultX);
    setYInput(defaultY);
    setZInput(defaultZ);
    setteam1PtsInput(defaultTeam1Pts);
    setteam1SetsInput(defaultTeam1Sets);
    setTeam1GamesInput(defaultTeam1Games);
    setteam2PtsInput(defaultTeam2Pts);
    setteam2SetsInput(defaultTeam2Sets);
    setTeam2GamesInput(defaultTeam2Games);
  };

  return (
    <div className="container py-5">
      <div className="row g-4">
        {/* Input Card */}
        <div className="col-md-6">
          <div className="card shadow-sm">
            <div className="card-header bg-secondary text-white">
              Input Values
            </div>
            <div className="card-body">
              <div className="row mb-3">
                <div className="col-4">
                  <label className="form-label">X Coordinate</label>
                  <input
                    className="form-control"
                    value={xInput}
                    onChange={(e) => setXInput(e.target.value)}
                  />
                </div>
                <div className="col-4">
                  <label className="form-label">Y Coordinate</label>
                  <input
                    className="form-control"
                    value={yInput}
                    onChange={(e) => setYInput(e.target.value)}
                  />
                </div>
                <div className="col-4">
                  <label className="form-label">Z Coordinate</label>
                  <input
                    className="form-control"
                    value={zInput}
                    onChange={(e) => setZInput(e.target.value)}
                  />
                </div>
              </div>

              <div className="row mb-3">
                <div className="col-4">
                  <label className="form-label">Team 1 Points</label>
                  <input
                    className="form-control"
                    value={team1PtsInput}
                    onChange={(e) => setteam1PtsInput(e.target.value)}
                  />
                </div>
                <div className="col-4">
                  <label className="form-label">Team 1 Sets</label>
                  <input
                    className="form-control"
                    value={team1SetsInput}
                    onChange={(e) => setteam1SetsInput(e.target.value)}
                  />
                </div>
                <div className="col-4">
                  <label className="form-label">Team 1 Games</label>
                  <input
                    className="form-control"
                    value={team1GamesInput}
                    onChange={(e) => setTeam1GamesInput(e.target.value)}
                  />
                </div>
              </div>

              <div className="row mb-3">
                <div className="col-4">
                  <label className="form-label">Team 2 Points</label>
                  <input
                    className="form-control"
                    value={team2PtsInput}
                    onChange={(e) => setteam2PtsInput(e.target.value)}
                  />
                </div>
                <div className="col-4">
                  <label className="form-label">Team 2 Sets</label>
                  <input
                    className="form-control"
                    value={team2SetsInput}
                    onChange={(e) => setteam2SetsInput(e.target.value)}
                  />
                </div>
                <div className="col-4">
                  <label className="form-label">Team 2 Games</label>
                  <input
                    className="form-control"
                    value={team2GamesInput}
                    onChange={(e) => setTeam2GamesInput(e.target.value)}
                  />
                </div>
              </div>

              <div className="d-grid mb-3">
                <button className="btn btn-primary" onClick={handlePublish}>
                  Send Values
                </button>
              </div>

              {/* Clear Inputs Button */}
              <div className="d-grid">
                <button className="btn btn-danger" onClick={handleClearInputs}>
                  Clear Inputs
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Live Values Card */}
        <div className="col-md-6">
          <div className="card shadow-sm">
            <div className="card-header bg-secondary text-white">
              Live MQTT Values
            </div>
            <div className="card-body">
              <ul className="list-group list-group-flush">
                <li className="list-group-item">
                  <strong>X:</strong> {liveX} mm
                </li>
                <li className="list-group-item">
                  <strong>Y:</strong> {liveY} mm
                </li>
                <li className="list-group-item">
                  <strong>Z:</strong> {liveZ} mm
                </li>
                <li className="list-group-item">
                  <strong>Centroid:</strong> {liveCentroid} mm
                </li>
                <li className="list-group-item">
                  <strong>Team 1 Points:</strong> {liveTeam1Pts}
                </li>
                <li className="list-group-item">
                  <strong>Team 1 Sets:</strong> {liveTeam1Sets}
                </li>
                <li className="list-group-item">
                  <strong>Team 1 Games:</strong> {liveTeam1Games}
                </li>
                <li className="list-group-item">
                  <strong>Team 2 Points:</strong> {liveTeam2Pts}
                </li>
                <li className="list-group-item">
                  <strong>Team 2 Sets:</strong> {liveTeam2Sets}
                </li>
                <li className="list-group-item">
                  <strong>Team 2 Games:</strong> {liveTeam2Games}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MQTTComponent;
