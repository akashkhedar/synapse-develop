import { motion, AnimatePresence, useScroll, useTransform } from "framer-motion";
import { useState, useRef, useEffect } from "react";
import { SmoothSection } from "./shared";

interface FeatureAccordionProps {
  number: string;
  title: string;
  description: string;
  isOpen: boolean;
  onClick: () => void;
}

const FeatureAccordion = ({ 
  number, 
  title, 
  description, 
  isOpen, 
  onClick 
}: FeatureAccordionProps) => {
  return (
    <motion.div
      className="border-b border-gray-800 cursor-pointer"
      onClick={onClick}
    >
      <div className="py-8 flex items-start gap-6">
        <span className="text-[#8b5cf6] text-base font-mono tracking-wider">{number}/</span>
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <h3 className="text-2xl md:text-3xl font-medium text-white">{title}</h3>
            <motion.span
              animate={{ rotate: isOpen ? 45 : 0 }}
              transition={{ duration: 0.2 }}
              className="text-gray-500 text-3xl font-light"
            >
              +
            </motion.span>
          </div>
          <AnimatePresence>
            {isOpen && (
              <motion.p
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
                className="text-gray-500 text-base mt-6 leading-relaxed overflow-hidden font-mono"
              >
                {description}
              </motion.p>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
};

export const FeaturesSection = () => {
  const [activeIndex, setActiveIndex] = useState(0);
  const sectionRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ["start start", "end end"]
  });

  const features = [
    {
      number: "01",
      title: "You bring models. We bring the compute.",
      description:
        "Get complete AI factories integrating high-density power, liquid cooling, and NVIDIA GPUs into one system designed for peak AI performance.",
      image: "https://wallpapers.com/images/hd/4k-tech-105e3a4x7aw7coqd.jpg",
    },
    {
      number: "02",
      title: "Your supercomputer. Your rules.",
      description:
        "Full control over your infrastructure with customizable configurations, dedicated resources, and direct access to hardware for maximum performance.",
      image: "https://cdn.wallpapersafari.com/64/96/9m8BVu.jpg",
    },
    {
      number: "03",
      title: "Orchestration, handled.",
      description:
        "Deploy and manage your ML workloads seamlessly with automated orchestration, load balancing, and intelligent resource allocation.",
      image:
        "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8aW5mb3JtYXRpb24lMjB0ZWNobm9sb2d5fGVufDB8fDB8fHww",
    },
    {
      number: "04",
      title: "Experts included.",
      description:
        "Work with our team of ML infrastructure specialists who understand your needs and help optimize your training pipelines from day one.",
      image: "https://wallpapers.com/images/hd/4k-tech-2k2jzc0qemh7y38n.jpg",
    },
  ];

  // Update active feature based on scroll progress
  useEffect(() => {
    const unsubscribe = scrollYProgress.on("change", (latest) => {
      const featureCount = features.length;
      const newIndex = Math.min(
        Math.floor(latest * featureCount),
        featureCount - 1
      );
      setActiveIndex(newIndex);
    });

    return () => unsubscribe();
  }, [scrollYProgress, features.length]);

  return (
    <div className="relative bg-black">
      {/* Heading section - scrolls normally */}
      <div className="min-h-screen flex items-center">
        <div className="max-w-7xl mx-auto px-6 w-full">
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white leading-tight max-w-2xl">
            Built for AI.
            <br />
            Ready for superintelligence.
          </h2>
        </div>
      </div>

      {/* Sticky scroll section - features + images */}
      <div ref={sectionRef} className="relative" style={{ height: "300vh" }}>
        <div className="sticky top-0 h-screen flex items-center">
          <div className="max-w-7xl mx-auto px-6 w-full">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
              {/* Left side - Features Accordion */}
              <div>
                {features.map((feature, index) => (
                  <FeatureAccordion
                    key={index}
                    {...feature}
                    isOpen={activeIndex === index}
                    onClick={() => setActiveIndex(index)}
                  />
                ))}
              </div>

              {/* Right side - Image Gallery with Scroll Sync */}
              <div className="relative h-[450px] hidden lg:block">
                <div className="h-full w-full">
                  <AnimatePresence mode="wait">
                    <motion.div
                      key={activeIndex}
                      initial={{ opacity: 0, y: 30 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -30 }}
                      transition={{ duration: 0.4, ease: "easeInOut" }}
                      className="w-full h-full"
                    >
                      <img
                        src={features[activeIndex].image}
                        alt={features[activeIndex].title}
                        className="w-full h-full object-cover rounded-lg border border-gray-800"
                      />
                    </motion.div>
                  </AnimatePresence>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
