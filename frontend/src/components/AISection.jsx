function AISection() {
  return (
    <section
      className="py-5"
      style={{
        background: "linear-gradient(135deg, #0d6efd, #4f8dfd)",
        color: "white",
      }}
    >
      <div className="container text-center">

        <h2 className="fw-bold display-5">
          🤖 NNRG AI Assistant
        </h2>

        <p className="lead mt-3">
          Ask anything about admissions, courses, placements,
          campus facilities, or upload a PDF and get instant answers.
        </p>

        <div className="row mt-5">

          <div className="col-md-3 mb-3">
            <h4>🎓</h4>
            <p>Admissions</p>
          </div>

          <div className="col-md-3 mb-3">
            <h4>📚</h4>
            <p>Courses</p>
          </div>

          <div className="col-md-3 mb-3">
            <h4>📄</h4>
            <p>PDF RAG</p>
          </div>

          <div className="col-md-3 mb-3">
            <h4>🌐</h4>
            <p>Website RAG</p>
          </div>

        </div>

        <button className="btn btn-light btn-lg mt-4">
          Launch AI Assistant
        </button>

      </div>
    </section>
  );
}

export default AISection;