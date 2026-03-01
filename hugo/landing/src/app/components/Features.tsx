import { motion } from "motion/react";
import { Play } from "lucide-react";
import { Button } from "./ui/button";

export function Features() {
  const features = [
    {
      title: "Task Distribution",
      description: "Split workloads across unlimited pods",
      color: "from-amber-400 to-orange-500",
    },
    {
      title: "Proxy Manager",
      description: "Automatic rotation and curation of proxies",
      color: "from-emerald-500 to-teal-600",
    },
    {
      title: "Anti-Detection",
      description: "Fingerprint spoofing and stealth mode",
      color: "from-rose-400 to-red-500",
    },
    {
      title: "Unlimited Scaling",
      description: "Kubernetes-native horizontal scaling",
      color: "from-slate-500 to-slate-700",
    },
    {
      title: "Centralized Monitoring",
      description: "Real-time dashboard for all pods",
      color: "from-cyan-400 to-teal-500",
    },
  ];

  return (
    <div className="py-40 px-6">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl lg:text-5xl font-bold mb-4 tracking-tight">Why Choose Armada?</h2>
          <p className="text-xl text-gray-500 max-w-2xl mx-auto font-light leading-relaxed">
            Everything you need to scale your bots and scrapers effortlessly.  
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-5 gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="bg-white/80 backdrop-blur-sm p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow"
            >
              <div className={`w-12 h-12 bg-gradient-to-br ${feature.color} rounded-lg mb-4`} />
              <h3 className="text-lg font-medium mb-2">{feature.title}</h3>
              <p className="text-gray-500 text-sm font-light leading-relaxed">{feature.description}</p>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="text-center mt-16"
        >
          <a href="https://github.com/user-attachments/assets/bfc55866-c84a-4ae2-a92b-2dfabf6c6350" target="_blank" rel="noopener noreferrer">
            <Button size="lg" variant="outline" className="gap-2">
              <Play className="w-4 h-4" />
              View quick video demo
            </Button>
          </a>
        </motion.div>
      </div>
    </div>
  );
}
