import { motion } from "motion/react";
import { Button } from "./ui/button";
import { Github, BookOpen } from "lucide-react";

export function Hero() {
  return (
    <div className="min-h-screen flex flex-col px-6 py-8">
      {/* Logo top-left */}
      <div>
        <img src="logo.png" alt="Armada" className="h-40 w-auto" />
      </div>

      <div className="flex-1 flex items-center">
        <div className="max-w-7xl w-full mx-auto grid lg:grid-cols-2 gap-12 items-center">
          {/* Left side - Title and CTA */}
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            className="space-y-6"
          >
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="inline-block px-4 py-2 bg-gray-100 text-gray-500 rounded-full text-sm"
              style={{ fontFamily: "var(--font-mono)" }}
            >
              Open Source • AGPL-3.0 License
            </motion.div>

            <h1 className="text-5xl lg:text-6xl font-bold leading-tight tracking-tight">
              Orchestrate your Bots and launch your{" "}
              <span className="text-gray-400">
              Armada
              </span>
            </h1>

            <p className="text-xl text-gray-600 font-light leading-relaxed">
              Write your bots and scrapers once, deploy them at any scale in seconds. Educational purposes.
            </p>

            <div className="flex flex-wrap gap-4">
              <a href="https://github.com/armadasvc/armada" target="_blank" rel="noopener noreferrer">
                <Button size="lg" className="gap-2">
                  <Github className="w-4 h-4" />
                  View on GitHub
                </Button>
              </a>
              <a href="docs">
                <Button size="lg" variant="outline" className="gap-2">
                  <BookOpen className="w-4 h-4" />
                  Read Documentation
                </Button>
              </a>
            </div>
          </motion.div>

          {/* Right side - Animation */}
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            className="relative"
          >
            <object
              data="animation.svg"
              type="image/svg+xml"
              className="w-full max-w-lg mx-auto rounded-xl shadow-lg overflow-hidden"
              style={{ aspectRatio: "600/900" }}
            />
          </motion.div>
        </div>
      </div>
    </div>
  );
}

