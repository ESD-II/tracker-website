import React, { useEffect, useState, useRef } from "react";
import mqtt from "mqtt";

const MQTTComponent = () => {
  const mqttClientRef = useRef(null);

  // Default input values
  const defaultServer = "0,0,0";
  const defaultTeam1Pts = "0";
  const defaultTeam1Sets = "0";
  const defaultTeam2Pts = "0";
  const defaultTeam2Sets = "0";
  const defaultTeam1Games = "0";
  const defaultTeam2Games = "0";

  // MQTT state
  const [liveServer, setLiveServer] = useState("");
  const [liveCentroid, setLiveCentroid] = useState("");
  const [liveTeam1Pts, setLiveTeam1Pts] = useState("");
  const [liveTeam1Sets, setLiveTeam1Sets] = useState("");
  const [liveTeam2Pts, setLiveTeam2Pts] = useState("");
  const [liveTeam2Sets, setLiveTeam2Sets] = useState("");
  const [liveTeam1Games, setLiveTeam1Games] = useState("");
  const [liveTeam2Games, setLiveTeam2Games] = useState("");

  const [serverInput, setServerInput] = useState(defaultServer);
  const [team1PtsInput, setTeam1PtsInput] = useState(defaultTeam1Pts);
  const [team1SetsInput, setTeam1SetsInput] = useState(defaultTeam1Sets);
  const [team2PtsInput, setTeam2PtsInput] = useState(defaultTeam2Pts);
  const [team2SetsInput, setTeam2SetsInput] = useState(defaultTeam2Sets);
  const [team1GamesInput, setTeam1GamesInput] = useState(defaultTeam1Games);
  const [team2GamesInput, setTeam2GamesInput] = useState(defaultTeam2Games);

  useEffect(() => {
    const mqttClient = mqtt.connect("benjaminf.net:1884");
    mqttClientRef.current = mqttClient;

    mqttClient.on("connect", () => {
      console.log("Connected to MQTT broker");
      mqttClient.subscribe(
        [
          "tennis/scoreboard/ball_coords",
          "Ball/centroid",
          "Team1/points",
          "Team1/sets",
          "Team1/games",
          "Team2/points",
          "Team2/sets",
          "Team2/games",
        ],
        (err, granted) => {
          if (err) {
            console.error(
              "Subscription error:",
              err
            ); /* Print error to the console */
          } else {
            console.log(
              "Subscribed to topics:",
              granted.map((g) => g.topic)
            );
          }
        }
      );
    });

    mqttClient.on("message", (topic, payload) => {
      const message = payload.toString();
      switch (topic) {
        case "tennis/scoreboard/ball_coords":
          setLiveServer(message);
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

    return () => {
      if (mqttClientRef.current) {
        mqttClientRef.current.end();
      }
    };
  }, []);

  const handlePublish = () => {
    const client = mqttClientRef.current;
    if (client && client.connected) {
      client.publish("Ball/centroid", "0");
      client.publish("Team1/points", team1PtsInput);
      client.publish("Team1/sets", team1SetsInput);
      client.publish("Team1/games", team1GamesInput);
      client.publish("Team2/points", team2PtsInput);
      client.publish("Team2/sets", team2SetsInput);
      client.publish("Team2/games", team2GamesInput);
    } else {
      console.log("MQTT client not connected.");
    }
  };

  const handleClearInputs = () => {
    setTeam1PtsInput(defaultTeam1Pts);
    setTeam1SetsInput(defaultTeam1Sets);
    setTeam1GamesInput(defaultTeam1Games);
    setTeam2PtsInput(defaultTeam2Pts);
    setTeam2SetsInput(defaultTeam2Sets);
    setTeam2GamesInput(defaultTeam2Games);
  };

  return (
    <div className="container py-5">
      <div className="row g-4">
        {/* Input Card */}
        <div className="col-md-6">
          <div className="card shadow-sm">
            <h1 className="card-header">Input Values</h1>
            <div className="card-body">
              {/* Team 1 Inputs */}
              <div className="row mb-3">
                <div className="col-4">
                  <label className="form-label">Team 1 Points</label>
                  <input
                    className="form-control"
                    value={team1PtsInput}
                    onChange={(e) => setTeam1PtsInput(e.target.value)}
                  />
                </div>
                <div className="col-4">
                  <label className="form-label">Team 1 Sets</label>
                  <input
                    className="form-control"
                    value={team1SetsInput}
                    onChange={(e) => setTeam1SetsInput(e.target.value)}
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

              {/* Team 2 Inputs */}
              <div className="row mb-3">
                <div className="col-4">
                  <label className="form-label">Team 2 Points</label>
                  <input
                    className="form-control"
                    value={team2PtsInput}
                    onChange={(e) => setTeam2PtsInput(e.target.value)}
                  />
                </div>
                <div className="col-4">
                  <label className="form-label">Team 2 Sets</label>
                  <input
                    className="form-control"
                    value={team2SetsInput}
                    onChange={(e) => setTeam2SetsInput(e.target.value)}
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
            <h1 className="card-header">Live MQTT Values</h1>
            <div className="card-body">
              <ul className="list-group list-group-flush">
                <li className="list-group-item">
                  <strong>Server:</strong> {liveServer}
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
