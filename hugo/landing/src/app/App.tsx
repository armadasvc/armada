import { Hero } from "./components/Hero";
import { Features } from "./components/Features";
import { DiagramSection } from "./components/DiagramSection";
import { SupportedDrivers } from "./components/SupportedDrivers";
import { CanvasBackground } from "./components/CanvasBackground";
import { Contact } from "./components/Contact";
import { UsefulLinks } from "./components/UsefulLinks";
import { Footer } from "./components/Footer";

export default function App() {
  return (
    <div className="size-full relative">
      <CanvasBackground />
      <div className="relative" style={{ zIndex: 1 }}>
      <Hero />
      
      <Features />
      
      <DiagramSection
        title="Distributed Architecture"
        description="A Kubernetes-based architecture that centralizes business logic and configuration management while distributing task execution across scalable workers."
        diagramSlot={
          <img
            src="deployment-flow.svg"
            alt="Deployment flow diagram"
            className="w-full rounded-xl"
          />
        }
        ctaLabel="View more architectural diagrams"
        ctaHref="https://github.com/armadasvc/armada?tab=readme-ov-file#under-the-hood"
      />

      <SupportedDrivers />

      <Contact />

      <UsefulLinks />

      <Footer />
      </div>
    </div>
  );
}