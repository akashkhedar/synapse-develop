import { motion } from "framer-motion";
import { SmoothSection } from "./shared";

export const StatsSection = () => {
  const stats = [
    { value: "10M+", label: "Annotations created" },
    { value: "99.9%", label: "Platform uptime" },
    { value: "500+", label: "Enterprise customers" },
    { value: "<50ms", label: "API response time" }
  ];

  return (
    <SmoothSection className="py-24 bg-black border-t border-gray-900">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              viewport={{ once: true }}
              className="text-center"
            >
              <div className="text-4xl md:text-5xl font-bold text-white mb-2">{stat.value}</div>
              <div className="text-gray-500 text-sm uppercase tracking-wider">{stat.label}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </SmoothSection>
  );
};
