function Placements() {
  return (
    <section
      id="placements"
      className="py-5 bg-light"
      style={{ scrollMarginTop: "90px" }}
    >
      <div className="container">

        <div className="text-center mb-5">
          <h2 className="fw-bold text-primary">
            Training & Placements
          </h2>

          <p className="text-muted">
            Helping students build successful careers through industry exposure,
            skill development, and placement assistance.
          </p>
        </div>

        <div className="row align-items-center">

          {/* Left Side */}
          <div className="col-lg-6">

            <h3 className="fw-bold mb-4">
              Building Future Professionals
            </h3>

            <p className="text-muted">
              NNRG College supports students with placement preparation,
              internships, aptitude training, soft skills, resume building,
              and career guidance to improve employability.
            </p>

            <div className="mt-4">

              <p>✅ Placement Assistance</p>

              <p>✅ Industry Interaction</p>

              <p>✅ Internship Opportunities</p>

              <p>✅ Career Guidance</p>

            </div>

          </div>

          {/* Right Side */}

          <div className="col-lg-6">

            <div className="row g-4">

              <div className="col-6">
                <div
                  className="card shadow border-0 text-center p-4 course-card"
                  style={{
                    borderRadius: "18px",
                    transition: "all 0.3s ease",
                    cursor: "pointer",
                  }}
>
                  <h2 className="text-primary fw-bold">100+</h2>
                  <p className="mb-0">Industry Partners</p>
                </div>
              </div>

              <div className="col-6">
                <div className="card shadow border-0 text-center p-4 course-card">
                  <h2 className="text-success fw-bold">Career</h2>
                  <p className="mb-0">Guidance Programs</p>
                </div>
              </div>

              <div className="col-6">
                <div className="card shadow border-0 text-center p-4 course-card">
                  <h2 className="text-warning fw-bold">Internship</h2>
                  <p className="mb-0">Support</p>
                </div>
              </div>

              <div className="col-6">
                <div className="card shadow border-0 text-center p-4 course-card">
                  <h2 className="text-danger fw-bold">Training</h2>
                  <p className="mb-0">Programs</p>
                </div>
              </div>

            </div>

          </div>

        </div>

      </div>
    </section>
  );
}

export default Placements;