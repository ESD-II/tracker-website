import React, { useEffect, useState, useRef } from "react";
import mqtt from "mqtt";

const MQTTComponent = () => {
  const mqttClientRef = useRef(null);
  const [xCoord, setXCoord] = useState("");
  const [yCoord, setYCoord] = useState("");
  const [zCoord, setZCoord] = useState("");
  const [centroidVal, setCentroidVal] = useState("");

  /* User Inputs */
  const [xInput, setXInput] = useState("");
  const [yInput, setYInput] = useState("");
  const [zInput, setZInput] = useState("");

  useEffect(() => {
    const mqttClient = mqtt.connect("ws://192.168.1.4:8885");
    mqttClientRef.current = mqttClient;

    mqttClient.on("connect", () => {
      console.log("Connected to MQTT broker");

      mqttClient.subscribe(
        [
          "Ball/xCoordinate",
          "Ball/yCoordinate",
          "Ball/zCoordinate",
          "Ball/centroid",
        ],
        (err) => {
          if (err) {
            console.log("Subscription failed: ", err);
          }
        }
      );
    });

    mqttClient.on("error", (err) => {
      console.error("MQTT Connection Error:", err);
    });

    mqttClient.on("message", (topic, payload) => {
      const message = payload.toString();
      console.log(`Message received on ${topic}: ${message}`);

      if (topic === "Ball/xCoordinate") {
        setXCoord(message);
      } else if (topic === "Ball/yCoordinate") {
        setYCoord(message);
      } else if (topic === "Ball/zCoordinate") {
        setZCoord(message);
      } else if (topic === "Ball/centroid") {
        setCentroidVal(message);
      }
    });

    return () => {
      mqttClient.end();
    };
  }, []);

  const handlePublish = () => {
    const client = mqttClientRef.current;
    if (client) {
      client.publish("Ball/xCoordinate", xInput);
      client.publish("Ball/yCoordinate", yInput);
      client.publish("Ball/zCoordinate", zInput);
      client.publish("Ball/centroid", "111");
    }
  };

  return (
    <div>
      <div>
        <div class="input-group input-group-sm mb-3">
          <span class="input-group-text" id="inputGroup-sizing-sm">
            Enter X Coordinate:{" "}
          </span>
          <input
            type="text"
            class="form-control"
            aria-label="Sizing example input"
            aria-describedby="inputGroup-sizing-sm"
            value={xInput}
            onChange={(e) => setXInput(e.target.value)}
          />
        </div>

        <div class="input-group input-group-sm mb-3">
          <span class="input-group-text" id="inputGroup-sizing-sm">
            Enter Y Coordinate:{" "}
          </span>
          <input
            type="text"
            class="form-control"
            aria-label="Sizing example input"
            aria-describedby="inputGroup-sizing-sm"
            value={yInput}
            onChange={(e) => setYInput(e.target.value)}
          />
        </div>

        <div class="input-group input-group-sm mb-3">
          <span class="input-group-text" id="inputGroup-sizing-sm">
            Enter Z Coordinate:{" "}
          </span>
          <input
            type="text"
            class="form-control"
            aria-label="Sizing example input"
            aria-describedby="inputGroup-sizing-sm"
            value={zInput}
            onChange={(e) => setZInput(e.target.value)}
          />
        </div>

        <button type="button" class="btn btn-primary" onClick={handlePublish}>
          Send Values
        </button>
      </div>

      <p>X Coordinate: {xCoord}</p>
      <p>Y Coordinate: {yCoord}</p>
      <p>Z Coordinate: {zCoord}</p>
      <p>Ball Centroid: {centroidVal}</p>
    </div>
  );
};

export default MQTTComponent;
