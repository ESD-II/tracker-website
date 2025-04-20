import "./Home.css";

import MQTTComponent from "./MQTTComponent";

function Home() {
  return (
    <main role="main">
      <div className="page-container">
        <h1 className="text-center">Live Data</h1>
        <MQTTComponent />
      </div>
    </main>
  );
}

export default Home;
