import { motion } from "framer-motion";
import { SmoothSection } from "./shared";

export const CTASection = () => {
  return (
    <SmoothSection className="py-32 bg-black border-t border-gray-900 relative overflow-hidden">
      {/* Background grid pattern */}
      <div className="absolute inset-0 opacity-[0.03]">
        <div 
          className="w-full h-full"
          style={{
            backgroundImage: `
              linear-gradient(to right, #ffffff 1px, transparent 1px),
              linear-gradient(to bottom, #ffffff 1px, transparent 1px)
            `,
            backgroundSize: '60px 60px'
          }}
        />
      </div>

      {/* Gradient glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-purple-500/10 rounded-full blur-[150px] pointer-events-none" />

      <div className="max-w-5xl mx-auto px-6 relative z-10">
        {/* Main content */}
        <div className="text-center mb-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
            className="inline-block mb-6"
          >
            <span className="text-gray-500 font-mono text-sm tracking-wider uppercase">
              pip install synapse-sdk
            </span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            viewport={{ once: true }}
            className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-8 leading-tight"
          >
            This is Synapse.
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400">
              Accelerate your Medical AI
            </span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            viewport={{ once: true }}
            className="text-gray-400 text-lg max-w-xl mx-auto mb-12 font-mono"
          >
            Create a project, connect your cloud storage, and get production-quality annotations delivered to your ML pipeline.
          </motion.p>

          {/* Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            viewport={{ once: true }}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            <motion.button
              whileHover={{ scale: 1.02, boxShadow: "0 0 30px rgba(139, 92, 246, 0.3)" }}
              whileTap={{ scale: 0.98 }}
              className="bg-white text-black px-10 py-4 text-base font-semibold hover:bg-gray-100 transition-all"
            >
              Create Free Account →
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.02, backgroundColor: "rgba(255,255,255,0.05)" }}
              whileTap={{ scale: 0.98 }}
              className="border border-gray-700 text-white px-10 py-4 text-base font-semibold transition-all"
            >
              Read SDK Docs
            </motion.button>
          </motion.div>
        </div>

        {/* Bottom stats */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          viewport={{ once: true }}
          className="flex flex-wrap justify-center gap-12 pt-12 border-t border-gray-800"
        >
          {[
            { value: "DICOM", label: "Native Support" },
            { value: "HIPAA", label: "Secure Infrastructure" },
            { value: "SOC 2", label: "Type II Ready" },
          ].map((stat, index) => (
            <div key={index} className="text-center">
              <div className="text-3xl font-bold text-white mb-1">{stat.value}</div>
              <div className="text-gray-500 font-mono text-sm">{stat.label}</div>
            </div>
          ))}
        </motion.div>
      </div>
    </SmoothSection>
  );
};
