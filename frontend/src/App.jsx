import { useState } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";

import NavigationBar from "./components/navigation/NavigationBar.jsx";
import Footer from "./components/footer/Footer.jsx";
import NotFound from "./components/notfound/NotFound.jsx";
import Replay from "./components/replay/Replay";

function App() {
  const [count, setCount] = useState(0);

  return (
    <div className="page-container">
      {" "}
      {/* Flexbox Container */}
      <NavigationBar />
      <div className="content-wrap">
        {" "}
        {/* Ensures main content expands */}
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Replay />} />
            {/* Catch-all route for undefined pages */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </div>
      <Footer />
    </div>
  );
}

export default App;
