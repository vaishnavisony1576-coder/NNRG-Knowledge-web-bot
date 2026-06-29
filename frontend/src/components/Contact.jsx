function Contact() {
  return (
    <section
      id="contact"
      className="py-5"
      style={{ scrollMarginTop: "90px" }}
    >
      <div className="container">

        <div className="text-center mb-5">
          <h2 className="fw-bold text-primary">Contact Us</h2>
          <p className="text-muted">
            We'd love to hear from you. Get in touch with NNRG College.
          </p>
        </div>

        <div className="row g-4">

          {/* Contact Details */}

          <div className="col-lg-5">

            <div
              className="card border-0 shadow p-4 h-100"
              style={{ borderRadius: "18px" }}
            >

              <h3 className="mb-4 fw-bold">
                Contact Information
              </h3>

              <p>
                <i className="bi bi-geo-alt-fill text-danger me-2"></i>

                Chowdariguda,
                Ghatkesar,
                Hyderabad,
                Telangana
              </p>

              <p>
                <i className="bi bi-telephone-fill text-success me-2"></i>

                +91 XXXXX XXXXX
              </p>

              <p>
                <i className="bi bi-envelope-fill text-primary me-2"></i>

                info@nnrg.edu.in
              </p>

              <p>
                <i className="bi bi-clock-fill text-warning me-2"></i>

                Mon - Sat : 9:00 AM - 5:00 PM
              </p>

            </div>

          </div>

          {/* Google Map Placeholder */}

          <div className="col-lg-7">

            <div
              className="card border-0 shadow h-100"
              style={{ borderRadius: "18px" }}
            >

              <div
                className="d-flex justify-content-center align-items-center"
                style={{
                  height: "320px",
                  background: "#f8f9fa",
                  borderRadius: "18px",
                }}
              >

                <iframe
                  src="https://www.google.com/maps?q=NNRG+College+Hyderabad&output=embed"
                  width="100%"
                  height="320"
                  style={{
                   border: 0,
                   borderRadius: "18px",
                  }}
                  loading="lazy"
                ></iframe>

              </div>

            </div>

          </div>

        </div>

      </div>
    </section>
  );
}

export default Contact;