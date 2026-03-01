import { motion } from "motion/react";
import { Mail } from "lucide-react";

export function Contact() {
  return (
    <div className="py-40 px-6">
      <div className="max-w-2xl mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-4xl lg:text-5xl font-bold mb-6 tracking-tight">
            Get in Touch
          </h2>
          <p className="text-lg text-gray-500 font-light leading-relaxed mb-8">
            Have a question, want to contribute, or just want to say hello?
            We'd love to hear from you.
          </p>
          <a
            href="mailto:contact@armada.services"
            className="inline-flex items-center gap-3 text-lg font-medium hover:opacity-70 transition-opacity"
            style={{ fontFamily: "var(--font-mono)" }}
          >
            <Mail className="w-5 h-5" />
            contact@armada.services
          </a>
        </motion.div>
      </div>
    </div>
  );
}
