function About() {
  return (
    <section id="about" className="py-5 bg-light">
      <div className="container">

        <div className="text-center mb-5">
          <h2 className="fw-bold text-primary">About NNRG College</h2>
          <p className="text-muted">
            NNRG Institutions are committed to delivering quality education,
            innovation, research, and industry-oriented learning to empower
            future professionals.
          </p>
        </div>

        <div className="row g-4">

          <div className="col-md-4">
            <div
  className="card border-0 shadow h-100 text-center p-4 course-card"
  style={{
    borderRadius: "18px",
    transition: "all 0.3s ease",
    cursor: "pointer",
  }}
>
              <i className="bi bi-bullseye display-3 text-primary"></i>

              <h4 className="mt-3">Vision</h4>

              <p className="text-muted">
                To become a premier institution recognized for academic
                excellence, innovation, research, and ethical values.
              </p>
            </div>
          </div>

          <div className="col-md-4">
            <div
              className="card border-0 shadow h-100 text-center p-4 course-card"
              style={{
                borderRadius: "18px",
                transition: "all 0.3s ease",
                cursor: "pointer",
              }}
            >
              <i className="bi bi-rocket-takeoff display-3 text-success"></i>

              <h4 className="mt-3">Mission</h4>

              <p className="text-muted">
                To nurture talented students through quality education,
                practical learning, and strong industry collaboration.
              </p>
            </div>
          </div>

          <div className="col-md-4">
            <div
              className="card border-0 shadow h-100 text-center p-4 course-card"
              style={{
                borderRadius: "18px",
                transition: "all 0.3s ease",
                cursor: "pointer",
               }}
            >
              <i className="bi bi-award display-3 text-warning"></i>

              <h4 className="mt-3">Why Choose NNRG?</h4>

              <p className="text-muted">
                Experienced faculty, modern laboratories, placement training,
                innovation, and an excellent campus environment.
              </p>
            </div>
          </div>

        </div>

      </div>
    </section>
  );
}

export default About;