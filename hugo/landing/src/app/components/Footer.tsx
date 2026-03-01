import { Github, Mail } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-gray-900 text-white py-12 px-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex flex-col items-center text-center gap-6 mb-10">
          <img src="logo-footer.png" alt="Armada" className="h-28 w-auto" />
          <p className="text-gray-400 font-light text-sm">
            Scale Your Bots & Scrapers. Effortlessly.
          </p>
          <a
            href="mailto:contact@armada.services"
            className="text-gray-400 hover:text-white transition-colors text-sm inline-flex items-center gap-2"
            style={{ fontFamily: "var(--font-mono)" }}
          >
            <Mail className="w-4 h-4" />
            contact@armada.services
          </a>
        </div>

        <div className="border-t border-gray-800 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-gray-500 text-xs" style={{ fontFamily: "var(--font-mono)" }}>
            © 2026 Armada — AGPL-3.0 License
          </p>
          <div className="flex gap-4">
            <a href="https://github.com/armadasvc/armada" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white transition-colors">
              <Github className="w-5 h-5" />
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
