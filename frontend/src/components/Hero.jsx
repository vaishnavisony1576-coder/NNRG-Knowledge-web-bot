function Hero() {
  return (
    <section
      id="home"
      className="text-white d-flex align-items-center"
      style={{
        minHeight: "90vh",
        background:
          "linear-gradient(rgba(0,0,0,0.65), rgba(0,0,0,0.65)), url('/images/campus1.webp') center/cover no-repeat",
      }}
    >
      <div className="container text-center">
        <h1
          className="display-3 fw-bold"
          style={{
          fontSize: "3.8rem",
          fontWeight: "700",
          lineHeight: "1.2",
          letterSpacing: "0.5px",
          }}
        >
          Nalla Narasimha Reddy 
          <br />
          Education Society's
          <br/>
          <span style={{ color: "#FFD54F" }}>
            Group of Institutions
          </span>
          
        </h1>

       <p
          className="mt-4"
          style={{
            fontSize: "1.25rem",
            fontWeight: "400",
            lineHeight: "1.6",
          }}
        >
          Building Future Leaders Through
          <br />
          <span style={{ color: "#FFD54F" }}>
            Quality Education • Innovation • Research • Excellence
          </span>
        </p>

        <div className="mt-5">
          <a
            href="#facilities"
            className="btn btn-warning btn-lg px-4 py-2 me-3 rounded-3"
          >
            Explore Campus
          </a>

          <a
            href="#courses"
            className="btn btn-outline-light btn-lg px-4 py-2 rounded-3"
          >
           Courses Offered
          </a>
        </div>
      </div>
    </section>
  );
}

export default Hero;