import React from "react";
import { Container } from "react-bootstrap";
import { FaGithub, FaLinkedin, FaEnvelope } from "react-icons/fa";
import "../styles/Footer.css";

function Footer() {
  return (
    <footer className="footer bg-primary text-center mt-4">
      <Container className="footer-content">
        <p>&copy; Diego Lopez 2025</p>
      </Container>
    </footer>
  );
}

export default Footer;
