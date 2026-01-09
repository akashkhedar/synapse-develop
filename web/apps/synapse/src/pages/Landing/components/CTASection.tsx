import { motion } from "framer-motion";
import { SmoothSection } from "./shared";

export const CTASection = () => {
  return (
    <SmoothSection className="py-32 bg-black border-t border-gray-900">
      <div className="max-w-4xl mx-auto px-6 text-center">
        <h2 className="text-4xl md:text-6xl font-bold text-white mb-6">
          Start building better AI
        </h2>
        <p className="text-xl text-gray-400 mb-12 max-w-2xl mx-auto">
          Join thousands of AI teams using Synapse to create high-quality training data.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="bg-white text-black px-8 py-4 rounded-lg text-base font-semibold hover:bg-gray-100 transition-all"
          >
            Get Started Free
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="border border-gray-700 text-white px-8 py-4 rounded-lg text-base font-semibold hover:bg-white/5 transition-all"
          >
            Schedule Demo
          </motion.button>
        </div>
      </div>
    </SmoothSection>
  );
};
