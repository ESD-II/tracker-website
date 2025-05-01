import React from "react";
import { Navbar, Container, Nav } from "react-bootstrap";
import { FaGithub, FaLinkedin } from "react-icons/fa";

function NavigationBar() {
  return (
    <Navbar bg="dark" variant="dark" expand="lg" fixed="top">
      <Container fluid>
        <Navbar.Brand href="/">Man I Love Firmware</Navbar.Brand>
        <Navbar.Toggle aria-controls="navbarSupportedContent" />
        <Navbar.Collapse id="navbarSupportedContent">
          <Nav className="me-auto">
          </Nav>

          {/* Right side GitHub, LinkedIn, and Admin Login */}
          <Nav className="ms-auto">
            <Nav.Link href="https://github.com/ESD-II" target="_blank">
              <FaGithub size={30} />
            </Nav.Link>
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
}

export default NavigationBar;
