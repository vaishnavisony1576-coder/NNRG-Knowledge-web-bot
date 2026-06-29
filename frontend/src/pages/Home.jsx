import Hero from "../components/Hero";
import About from "../components/About";
import Courses from "../components/Courses";
import Facilities from "../components/Facilities";
import Admissions from "../components/Admissions";
import Placements from "../components/Placements";
import Contact from "../components/Contact";

function Home() {
  return (
    <>
      <Hero />
      <About />
      <Courses />
      <Facilities />
      <Admissions />
      <Placements />
      <Contact />
    </>
  );
}

export default Home;