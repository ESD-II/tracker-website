import React, { useState, useEffect, useCallback, useRef } from "react";
import mqtt from "mqtt"; // Import mqtt directly

const MQTTComponent = () => {
  const [client, setClient] = useState(null);
  const [connectStatus, setConnectStatus] = useState("Connect");
  const [msg, setMsg] = useState("");
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(""); // For handling errors
  const mqttBrokerUrl = "ws://192.168.1.4:8885"; // Update this with actual URL
  const mqttTopic = "cameras/ws"; // Update this with your actual topic

  const clientRef = useRef(null); // To persist the client across renders

  const mqttConnect = useCallback(() => {
    setConnectStatus("Connecting...");
    setError(""); // Reset error message on every connection attempt

    const newClient = mqtt.connect(mqttBrokerUrl, {
      reconnectPeriod: 1000, // Attempt reconnect every 1 second if disconnected
    });

    clientRef.current = newClient;

    newClient.on("connect", () => {
      setConnectStatus("Connected");
      console.log("MQTT Connected");

      // Subscribe after successful connection
      if (newClient.connected) {
        newClient.subscribe(mqttTopic, (err) => {
          if (err) {
            console.error("Subscription error:", err);
            setError("Failed to subscribe.");
          } else {
            console.log("Subscribed to topic:", mqttTopic);
          }
        });
      } else {
        console.warn("Client not connected yet, retrying subscription.");
      }
    });

    newClient.on("error", (err) => {
      console.error("MQTT Connection Error:", err);
      setError("Could not connect.");
      newClient.end(); // Disconnecting client to trigger a reconnection attempt
    });

    newClient.on("message", (topic, message) => {
      setMessages((prevMessages) => [...prevMessages, message.toString()]);
    });

    // Handle disconnection and attempt to reconnect automatically
    newClient.on("close", () => {
      console.log("MQTT client disconnected.");
      setConnectStatus("Disconnected. Reconnecting...");
    });

    newClient.on("reconnect", () => {
      console.log("Reconnecting to MQTT...");
      setConnectStatus("Reconnecting...");
    });

    newClient.on("offline", () => {
      console.log("MQTT client is offline.");
      setConnectStatus("Offline");
    });

    setClient(newClient); // Update the state with the new client
  }, [mqttBrokerUrl, mqttTopic]);

  useEffect(() => {
    mqttConnect();
    return () => {
      console.log("Cleaning up MQTT");
      if (clientRef.current) {
        clientRef.current.end(); // Clean up the client on unmount
      }
    };
  }, [mqttConnect]);

  const handleInputChange = (event) => {
    setMsg(event.target.value);
  };

  const publishMessage = () => {
    if (client && connectStatus === "Connected") {
      client.publish(mqttTopic, msg);
      setMsg(""); // Clear the input field after publishing
    } else {
      setError("Not connected to the MQTT broker.");
    }
  };

  return (
    <div>
      <div>Connection Status: {connectStatus}</div>
      {error && <div style={{ color: "red" }}>Error: {error}</div>}
      <div>
        <input
          type="text"
          value={msg}
          onChange={handleInputChange}
          placeholder="Enter message"
        />
        <button
          onClick={publishMessage}
          disabled={connectStatus !== "Connected"}
        >
          Publish
        </button>
      </div>
      <div>
        {messages.map((message, index) => (
          <p key={index}>{message}</p>
        ))}
      </div>
    </div>
  );
};

export default MQTTComponent;
