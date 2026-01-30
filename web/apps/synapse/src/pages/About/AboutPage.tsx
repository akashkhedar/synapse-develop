import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Navigation } from "../Landing/components/Navigation";
import { Footer } from "../Landing/components/Footer";
import { SmoothSection } from "../Landing/components/shared";
import type { Page } from "../types/Page";

export const AboutPage: Page = {
  path: "/about",
  title: "About",
  component: () => {
    const [isHiringModalOpen, setIsHiringModalOpen] = useState(false);

    const stats = [
    { value: "2026", label: "Founded" },
    { value: "HIPAA", label: "Compliant Platform" },
    { value: "SOC 2", label: "Type II Ready" },
    { value: "24/7", label: "Expert Support" },
  ];

  const values = [
    {
      number: "01",
      title: "Clinical Accuracy",
      description: "We obsess over diagnostic quality. Every annotation goes through multi-stage validation by board-certified specialists to ensure your models are trained on ground truth.",
    },
    {
      number: "02", 
      title: "Built for DICOM",
      description: "From 3D volumetric MRI to WSI pathology slides, our platform handles complex medical data formats natively without compromising speed or fidelity.",
    },
    {
      number: "03",
      title: "Patient First",
      description: "Privacy isn't a feature, it's our foundation. HIPAA compliance, SOC 2 Type II, and strict PHI protocols protect patient data at every layer.",
    },
  ];



  return (
    <div className="bg-black min-h-screen">
      <Navigation />
      
      {/* Hero Section */}
      <section className="relative min-h-[60vh] flex items-center justify-center overflow-hidden pt-32 pb-20">
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

        <div className="max-w-5xl mx-auto px-6 text-center relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mb-6"
          >
            <span className="text-gray-500 font-mono text-sm tracking-wider uppercase">
              // About Synapse
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-5xl md:text-6xl lg:text-7xl font-bold text-white mb-8 leading-tight"
          >
            Building the foundation
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400">
              for Healthcare AI
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-xl text-gray-400 max-w-3xl mx-auto font-mono"
          >
            We're on a mission to accelerate medical breakthroughs by providing 
            high-quality, clinically validated training data.
          </motion.p>
        </div>
      </section>

      {/* Stats Section */}
      <SmoothSection className="py-20 bg-black border-t border-gray-900">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-12">
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
                <div className="text-gray-500 font-mono text-sm">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </SmoothSection>

      {/* Our Story Section */}
      <SmoothSection className="py-32 bg-black border-t border-gray-900">
        <div className="max-w-4xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="mb-12"
          >
            <div className="flex items-start gap-4 mb-8">
              <div className="flex flex-col items-start">
                <div className="w-6 h-[2px] bg-gray-600" />
                <div className="w-[2px] h-6 bg-gray-600" />
              </div>
              <h2 className="text-4xl md:text-5xl font-bold text-white">Our Story</h2>
            </div>
            
            <div className="space-y-6 text-gray-400 font-mono text-lg leading-relaxed">
              <p>
                Synapse was born from a critical gap in medical AI development: the lack of access to 
                high-quality, expertly annotated medical imaging data.
              </p>
              <p>
                In 2026, our founders—a radiologist and a health-tech engineer—came together with a 
                vision to build the annotation infrastructure that the future of healthcare requires. 
                Existing tools couldn't handle DICOM complexities or HIPAA requirements.
              </p>
              <p>
                Today, we are building the platform to power clinical AI pipelines for top research 
                hospitals and biotech companies, bridging the gap between medical expertise and 
                machine learning innovation.
              </p>
            </div>
          </motion.div>
        </div>
      </SmoothSection>

      {/* Values Section */}
      <SmoothSection className="py-32 bg-black border-t border-gray-900">
        <div className="max-w-6xl mx-auto px-6">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="text-4xl md:text-5xl font-bold text-white mb-16"
          >
            What we believe
          </motion.h2>

          <div className="space-y-12">
            {values.map((value, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="border-l-2 border-gray-800 pl-8 hover:border-purple-500 transition-colors"
              >
                <div className="text-gray-500 font-mono text-sm mb-2">{value.number}/</div>
                <h3 className="text-2xl font-bold text-white mb-3">{value.title}</h3>
                <p className="text-gray-400 font-mono leading-relaxed">{value.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </SmoothSection>

      {/* CTA Section */}
      <SmoothSection className="py-32 bg-black border-t border-gray-900">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="text-4xl md:text-5xl font-bold text-white mb-6"
          >
            Join us in building the future of AI
          </motion.h2>
          
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            viewport={{ once: true }}
            className="text-gray-400 font-mono mb-12 text-lg"
          >
            We're always looking for talented people who share our vision.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            viewport={{ once: true }}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setIsHiringModalOpen(true)}
              className="bg-white text-black px-10 py-4 text-base font-semibold transition-all"
            >
              View Open Positions →
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.02, backgroundColor: "rgba(255,255,255,0.05)" }}
              whileTap={{ scale: 0.98 }}
              className="border border-gray-700 text-white px-10 py-4 text-base font-semibold transition-all"
            >
              Get in Touch
            </motion.button>
          </motion.div>
        </div>
      </SmoothSection>

      <Footer />

      <AnimatePresence>
        {isHiringModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div 
              className="absolute inset-0 bg-black/80 backdrop-blur-sm"
              onClick={() => setIsHiringModalOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative w-full max-w-md bg-black border border-gray-800 p-8 shadow-2xl"
            >
              {/* Corner Accents */}
              <div className="absolute top-0 left-0 w-4 h-[1px] bg-purple-500" />
              <div className="absolute top-0 left-0 w-[1px] h-4 bg-purple-500" />
              <div className="absolute bottom-0 right-0 w-4 h-[1px] bg-purple-500" />
              <div className="absolute bottom-0 right-0 w-[1px] h-4 bg-purple-500" />

              <div className="text-center">
                <div className="text-gray-500 font-mono text-xs uppercase tracking-wider mb-4">
                  // Status: Full Capacity
                </div>
                
                <h3 className="text-2xl font-bold text-white mb-4">
                  No Open Positions
                </h3>
                
                <p className="text-gray-400 font-mono text-sm leading-relaxed mb-8">
                  We are currently full and not seeking new team members at the moment. 
                  However, we are always growing—please check back soon!
                </p>

                <motion.button
                  whileHover={{ scale: 1.02, backgroundColor: "rgba(255,255,255,0.05)" }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setIsHiringModalOpen(false)}
                  className="w-full border border-gray-700 text-white px-6 py-3 text-sm font-semibold transition-all hover:border-gray-500"
                >
                  Close
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
    );
  },
};