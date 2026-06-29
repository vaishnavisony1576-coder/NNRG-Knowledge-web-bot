const courses = [
  {
    name: "AI & ML",
    fullName: "Artificial Intelligence & Machine Learning",
    icon: "bi-cpu",
    color: "primary",
  },
  {
    name: "CSE",
    fullName: "Computer Science & Engineering",
    icon: "bi-laptop",
    color: "info",
  },
  {
    name: "IT",
    fullName: "Information Technology",
    icon: "bi-globe",
    color: "success",
  },
  {
    name: "DS",
    fullName: "Data Science",
    icon: "bi-bar-chart",
    color: "warning",
  },
  {
    name: "ECE",
    fullName: "Electronics & Communication Engineering",
    icon: "bi-broadcast",
    color: "danger",
  },
  {
    name: "EEE",
    fullName: "Electrical & Electronics Engineering",
    icon: "bi-lightning",
    color: "secondary",
  },
  {
    name: "Civil",
    fullName: "Civil Engineering",
    icon: "bi-building",
    color: "dark",
  },
  {
    name: "Mechanical",
    fullName: "Mechanical Engineering",
    icon: "bi-gear",
    color: "primary",
  },
  {
    name: "MBA",
    fullName: "Master of Business Administration",
    icon: "bi-briefcase",
    color: "success",
  },
  {
    name: "Pharmacy",
    fullName: "Pharmacy",
    icon: "bi-capsule",
    color: "danger",
  },
];

function Courses() {
  return (
    <section id="courses" className="py-5">
      <div className="container">

        <div className="text-center mb-5">
          <h2 className="fw-bold text-primary">Courses Offered</h2>
          <p className="text-muted">
            Explore the diverse academic programs offered at NNRG Institutions.
          </p>
        </div>

        <div className="row g-4">
          {courses.map((course, index) => (
            <div className="col-lg-3 col-md-4 col-sm-6" key={index}>
              <div
                className="card border-0 shadow h-100 text-center p-4 course-card"
                style={{
                  borderRadius: "18px",
                  cursor: "pointer",
                }}
              >
                <i
                  className={`bi ${course.icon} display-4 text-${course.color}`}
                ></i>

                <h4 className="mt-3">{course.name}</h4>

                <p className="text-muted small flex-grow-1"
                   style={{minHeight:"60px"}}>
                  {course.fullName}
                </p>

                <button className="btn btn-outline-primary btn-sm mt-2">
                  Learn More
                </button>

              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}

export default Courses;