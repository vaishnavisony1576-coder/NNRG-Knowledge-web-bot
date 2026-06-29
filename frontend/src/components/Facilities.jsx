const facilities = [
  {
    name: "Library",
    icon: "bi-book",
    color: "primary",
    description: "Well-stocked library with books, journals, and digital resources.",
  },
  {
    name: "Computer Labs",
    icon: "bi-pc-display",
    color: "success",
    description: "Modern computer laboratories with the latest software and internet.",
  },
  {
    name: "Hostel",
    icon: "bi-house-door",
    color: "warning",
    description: "Comfortable hostel facilities with security and essential amenities.",
  },
  {
    name: "Transport",
    icon: "bi-bus-front",
    color: "danger",
    description: "College buses covering multiple routes for students and staff.",
  },
  {
    name: "Sports",
    icon: "bi-trophy",
    color: "info",
    description: "Indoor and outdoor sports facilities for physical fitness and recreation.",
  },
  {
    name: "Cafeteria",
    icon: "bi-cup-hot",
    color: "secondary",
    description: "Hygienic cafeteria serving fresh and affordable meals.",
  },
];

function Facilities() {
  return (
    <section
      id="facilities"
      className="py-5 bg-light"
      style={{ scrollMarginTop: "90px" }}
    >
      <div className="container">

        <div className="text-center mb-5">
          <h2 className="fw-bold text-primary">Campus Facilities</h2>
          <p className="text-muted">
            NNRG provides a modern campus with facilities that support learning,
            innovation, and student life.
          </p>
        </div>

        <div className="row g-4">
          {facilities.map((facility, index) => (
            <div className="col-lg-4 col-md-6" key={index}>
              <div
                className="card border-0 shadow h-100 text-center p-4 course-card"
                style={{
                  borderRadius: "18px",
                  cursor: "pointer",
                }}
              >
                <i
                  className={`bi ${facility.icon} display-4 text-${facility.color}`}
                ></i>

                <h4 className="mt-3">{facility.name}</h4>

                <p className="text-muted">
                  {facility.description}
                </p>

              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}

export default Facilities;