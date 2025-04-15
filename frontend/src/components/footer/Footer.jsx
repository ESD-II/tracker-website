import React from "react";
import { Container } from "react-bootstrap";
import { FaGithub, FaLinkedin, FaEnvelope } from "react-icons/fa";
import "./Footer.css";

function Footer() {
  return (
    <footer className="footer text-center mt-3">
      <Container className="footer-content">
        <p>&copy; Man I Love Firmware 2025</p>
        <div className="flex justify-center items-center gap-1 mb-1">
          <a
            href="https://github.com/ESD-II"
            target="_blank"
            rel="noopener noreferrer"
            className="text-white hover:text-yellow-400 transition-colors"
          >
            <FaGithub size={30} />
          </a>
        </div>
      </Container>
    </footer>
  );
}

export default Footer;
