import { motion } from "motion/react";
import { Images } from "lucide-react";
import { Button } from "./ui/button";

interface DiagramSectionProps {
  title: string;
  description: string;
  diagramSlot: React.ReactNode;
  ctaLabel?: string;
  ctaHref?: string;
}

export function DiagramSection({
  title,
  description,
  diagramSlot,
  ctaLabel,
  ctaHref,
}: DiagramSectionProps) {
  return (
    <div className="py-40 px-6">
      <div className="max-w-4xl mx-auto">
        {/* Text — full width, centered */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl lg:text-5xl font-bold mb-6 tracking-tight">
            {title}
          </h2>
          <p className="text-xl text-gray-500 max-w-2xl mx-auto leading-relaxed">
            {description}
          </p>
        </motion.div>

        {/* Diagram — below */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.15 }}
        >
          {diagramSlot}
        </motion.div>

        {ctaLabel && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="text-center mt-12"
          >
            <a href={ctaHref || "#"} target="_blank" rel="noopener noreferrer">
              <Button size="lg" variant="outline" className="gap-2">
                <Images className="w-4 h-4" />
                {ctaLabel}
              </Button>
            </a>
          </motion.div>
        )}
      </div>
    </div>
  );
}
