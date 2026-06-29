function Navbar() {
  return (
    <nav
      className="navbar navbar-expand-lg navbar-dark bg-primary fixed-top shadow-sm"
      style={{ padding: "12px 0" }}
    >
      <div className="container">

        <a className="navbar-brand fw-bold" href="#home">
          <span
            style={{
              fontSize: "1.5rem",
              fontWeight: "700",
              letterSpacing: "0.5px",
            }}
          >
            NNRG Institutions
          </span>
        </a>

        <button
          className="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navbarNav"
        >
          <span className="navbar-toggler-icon"></span>
        </button>

        <div className="collapse navbar-collapse" id="navbarNav">
          <ul className="navbar-nav ms-auto">

            <li className="nav-item">
              <a className="nav-link fw-semibold" href="#home">
                Home
              </a>
            </li>

            <li className="nav-item">
              <a className="nav-link fw-semibold" href="#about">
                About
              </a>
            </li>

            <li className="nav-item">
              <a className="nav-link fw-semibold" href="#courses">
                Courses
              </a>
            </li>

            <li className="nav-item">
              <a className="nav-link fw-semibold" href="#facilities">
                Facilities
              </a>
            </li>

            <li className="nav-item">
              <a className="nav-link fw-semibold" href="#admissions">
                Admissions
              </a>
            </li>

            <li className="nav-item">
              <a className="nav-link fw-semibold" href="#placements">
                Placements
              </a>
            </li>

            <li className="nav-item">
              <a className="nav-link fw-semibold" href="#contact">
                Contact
              </a>
            </li>

          </ul>
        </div>

      </div>
    </nav>
  );
}

export default Navbar;