import { motion } from "framer-motion";
import { SmoothSection } from "./shared";

export const TrustSection = () => {
  return (
    <SmoothSection className="py-32 bg-black border-t border-gray-900">
      <div className="max-w-5xl mx-auto px-6 text-center">
        <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
          Secure by design.
          <br />
          <span className="text-gray-500">Enterprise-ready by default.</span>
        </h2>
        <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-12">
          SOC 2 Type II certified. GDPR compliant. Your data stays your data
          with single-tenant deployment options.
        </p>
        
        <div className="flex flex-wrap justify-center gap-6">
          {["SOC 2", "GDPR", "HIPAA Ready", "ISO 27001"].map((badge, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, scale: 0.8 }}
              whileInView={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 }}
              viewport={{ once: true }}
              className="bg-gray-900 border border-gray-800 px-6 py-3 rounded-lg"
            >
              <span className="text-gray-300 font-medium">{badge}</span>
            </motion.div>
          ))}
        </div>
      </div>
    </SmoothSection>
  );
};
