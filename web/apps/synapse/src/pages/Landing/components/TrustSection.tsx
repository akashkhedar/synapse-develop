import { motion } from "framer-motion";
import { SmoothSection } from "./shared";

// Floating pixel decorations
const FloatingPixels = () => {
  const pixels = [
    { x: "10%", y: "30%", size: 4, color: "#ffffff", opacity: 0.3 },
    { x: "15%", y: "60%", size: 3, color: "#ffffff", opacity: 0.2 },
    { x: "20%", y: "75%", size: 5, color: "#10b981", opacity: 0.6 },
    { x: "25%", y: "45%", size: 3, color: "#ffffff", opacity: 0.15 },
    { x: "35%", y: "35%", size: 4, color: "#8b5cf6", opacity: 0.5 },
    { x: "40%", y: "70%", size: 3, color: "#ffffff", opacity: 0.2 },
    { x: "45%", y: "55%", size: 6, color: "#3b82f6", opacity: 0.4 },
    { x: "55%", y: "40%", size: 3, color: "#ffffff", opacity: 0.25 },
    { x: "60%", y: "65%", size: 4, color: "#ec4899", opacity: 0.5 },
    { x: "65%", y: "30%", size: 3, color: "#ffffff", opacity: 0.2 },
    { x: "70%", y: "50%", size: 5, color: "#10b981", opacity: 0.4 },
    { x: "75%", y: "75%", size: 4, color: "#ffffff", opacity: 0.3 },
    { x: "80%", y: "35%", size: 6, color: "#8b5cf6", opacity: 0.5 },
    { x: "85%", y: "60%", size: 3, color: "#ffffff", opacity: 0.2 },
    { x: "90%", y: "45%", size: 4, color: "#3b82f6", opacity: 0.4 },
  ];

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {pixels.map((pixel, i) => (
        <motion.div
          key={i}
          className="absolute"
          style={{
            left: pixel.x,
            top: pixel.y,
            width: pixel.size,
            height: pixel.size,
            backgroundColor: pixel.color,
            opacity: pixel.opacity,
            willChange: "opacity, transform",
          }}
          animate={{
            opacity: [pixel.opacity * 0.5, pixel.opacity, pixel.opacity * 0.5],
            scale: [0.9, 1, 0.9],
          }}
          transition={{
            duration: 4 + Math.random() * 3,
            repeat: Infinity,
            delay: Math.random() * 3,
            ease: "linear",
          }}
        />
      ))}
    </div>
  );
};

export const TrustSection = () => {
  const features = [
    {
      number: "01",
      title: "Data Never Leaves Your Cloud",
      description:
        "Connect directly to your S3, GCS, or Azure storage. Annotators work through secure presigned URLs — raw data stays in your infrastructure.",
    },
    {
      number: "02",
      title: "Elastic Clinical Workforce",
      description:
        "From 100 to 1M+ tasks, scale annotation capacity on-demand. Trained domain experts for radiology, pathology, dermatology, and more.",
    },
    {
      number: "03",
      title: "Transparent Credit-Based Billing",
      description:
        "Pay only for completed annotations. Project expenditures, real-time cost tracking, and detailed breakdowns per annotation type.",
    },
  ];

  return (
    <SmoothSection className="py-32 bg-black border-t border-gray-900 relative min-h-screen">
      <FloatingPixels />
      
      <div className="max-w-6xl mx-auto px-6 relative z-10">
        {/* Header */}
        <div className="mb-20">
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6 leading-tight">
            Secure. Scalable.
            <br />
            Specialized.
          </h2>
          
          {/* Corner bracket with subtitle */}
          <div className="flex items-start gap-4 mt-8">
            <div className="flex flex-col items-start">
              <div className="w-6 h-[2px] bg-gray-600" />
              <div className="w-[2px] h-6 bg-gray-600" />
            </div>
            <p className="text-gray-400 font-mono text-sm max-w-md">
              Security, compliance, and scale built into every clinical workflow.
            </p>
          </div>
        </div>

        {/* Cards in asymmetric layout */}
        <div className="relative">
          {/* Row 1: Cards 01 and 03 */}
          <div className="flex justify-between gap-8 mb-8">
            {/* Card 01 - Left */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              viewport={{ once: true }}
              className="w-full max-w-sm border border-gray-800 bg-black/50 p-6"
            >
              <div className="text-gray-500 font-mono text-sm mb-4">
                {features[0].number}/
              </div>
              <h3 className="text-white font-bold text-xl mb-4">
                {features[0].title}
              </h3>
              <p className="text-gray-500 text-sm leading-relaxed font-mono">
                {features[0].description}
              </p>
            </motion.div>

            {/* Spacer for asymmetry */}
            <div className="hidden md:block w-32" />

            {/* Card 03 - Right */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              viewport={{ once: true }}
              className="w-full max-w-sm border border-gray-800 bg-black/50 p-6"
            >
              <div className="text-gray-500 font-mono text-sm mb-4">
                {features[2].number}/
              </div>
              <h3 className="text-white font-bold text-xl mb-4">
                {features[2].title}
              </h3>
              <p className="text-gray-500 text-sm leading-relaxed font-mono">
                {features[2].description}
              </p>
            </motion.div>
          </div>

          {/* Row 2: Card 02 - Center */}
          <div className="flex justify-center">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              viewport={{ once: true }}
              className="w-full max-w-sm border border-gray-800 bg-black/50 p-6"
            >
              <div className="text-gray-500 font-mono text-sm mb-4">
                {features[1].number}/
              </div>
              <h3 className="text-white font-bold text-xl mb-4">
                {features[1].title}
              </h3>
              <p className="text-gray-500 text-sm leading-relaxed font-mono">
                {features[1].description}
              </p>
            </motion.div>
          </div>
        </div>
      </div>
    </SmoothSection>
  );
};
