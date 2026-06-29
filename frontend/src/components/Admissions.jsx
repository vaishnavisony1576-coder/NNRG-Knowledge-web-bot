const admissionSteps = [
  {
    icon: "bi-person-check",
    title: "Check Eligibility",
    description: "Verify the eligibility criteria for your chosen program.",
  },
  {
    icon: "bi-file-earmark-text",
    title: "Submit Application",
    description: "Complete the online application form with required details.",
  },
  {
    icon: "bi-patch-check",
    title: "Document Verification",
    description: "Upload and verify all academic and personal documents.",
  },
  {
    icon: "bi-mortarboard",
    title: "Confirm Admission",
    description: "Pay the admission fee and begin your academic journey.",
  },
];

function Admissions() {
  return (
    <section
      id="admissions"
      className="py-5"
      style={{ scrollMarginTop: "90px" }}
    >
      <div className="container">

        <div className="text-center mb-5">
          <h2 className="fw-bold text-primary">Admission Process</h2>
          <p className="text-muted">
            Join NNRG College in four simple steps.
          </p>
        </div>

        <div className="row g-4">
          {admissionSteps.map((step, index) => (
            <div className="col-lg-3 col-md-6" key={index}>
              <div
                className="card border-0 shadow h-100 text-center p-4 course-card"
                style={{
                  borderRadius: "18px",
                  transition:"all 0.3s ease",
                  cursor: "pointer",
                }}
              >
                <div
                  className="rounded-circle bg-primary text-white d-flex justify-content-center align-items-center mx-auto mb-3"
                  style={{
                    width: "60px",
                    height: "60px",
                    fontSize: "24px",
                  }}
                >
                  {index + 1}
                </div>

                <i
                  className={`bi ${step.icon} display-5 text-primary mb-3`}
                ></i>

                <h4>{step.title}</h4>

                <p className="text-muted">
                  {step.description}
                </p>
              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}

export default Admissions;