import { motion } from "motion/react";
import { Github, BookOpen, Map, Users, Scale, Play } from "lucide-react";

const links = [
  { label: "Github", icon: Github, href: "https://github.com/armadasvc/armada" },
  { label: "Documentation", icon: BookOpen, href: "docs" },
  { label: "Next Steps (Roadmap)", icon: Map, href: "docs/reference/next-steps/" },
  { label: "Contributing", icon: Users, href: "https://github.com/armadasvc/armada/blob/master/CONTRIBUTING.md" },
  { label: "License", icon: Scale, href: "https://github.com/armadasvc/armada/blob/master/LICENSE" },
  { label: "Demo Video", icon: Play, href: "https://github.com/user-attachments/assets/bfc55866-c84a-4ae2-a92b-2dfabf6c6350" },
];

export function UsefulLinks() {
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
            Useful Links
          </h2>
        </motion.div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 max-w-2xl mx-auto">
          {links.map((link, index) => (
            <motion.a
              key={link.label}
              href={link.href}
              target="_blank"
              rel="noopener noreferrer"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: index * 0.07 }}
              className="flex items-center gap-3 px-5 py-4 rounded-lg bg-white/80 backdrop-blur-sm shadow-sm hover:shadow-md transition-shadow text-gray-700 hover:text-gray-900"
            >
              <link.icon className="w-5 h-5 text-gray-400" />
              <span className="font-medium text-sm">{link.label}</span>
            </motion.a>
          ))}
        </div>
      </div>
    </div>
  );
}
