import { motion } from "motion/react";
import { Code } from "lucide-react";
import { Button } from "./ui/button";

export function SupportedDrivers() {
  return (
    <div className="py-40 px-6">
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <h2 className="text-4xl lg:text-5xl font-bold mb-6 tracking-tight">
            Supported Drivers
          </h2>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto font-light leading-relaxed">
            Armada is compatible with the most popular Python browser automation
            drivers out of the box.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="mb-12"
        >
          <img
            src="supported-drivers.png"
            alt="Supported drivers overview"
            className="w-full rounded-xl"
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="max-w-2xl mx-auto"
        >
          <p className="text-base text-gray-500 font-light leading-relaxed">
            Fantomas is Armada's in-house browser automation library built on
            top of nodriver, designed to emulate realistic human behavior (curved
            mouse movements and randomized typing delays) through either native
            CDP control or OS-level input via xdotool.
          </p>
          <p className="text-base text-gray-500 font-light leading-relaxed mt-4">
            It integrates with Armada's two-tier lifecycle by reusing a single
            browser instance at the agent level while remaining fully compatible
            with the standard nodriver API.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="text-center mt-12"
        >
          <a href="https://github.com/armadasvc/armada/tree/master/lib" target="_blank" rel="noopener noreferrer">
            <Button size="lg" variant="outline" className="gap-2">
              <Code className="w-4 h-4" />
              View Fantomas Source Code
            </Button>
          </a>
        </motion.div>
      </div>
    </div>
  );
}
