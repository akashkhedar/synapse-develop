import { motion, AnimatePresence, useScroll, useTransform } from "framer-motion";
import { useState, useRef, useEffect } from "react";
import { SmoothSection } from "./shared";
import image1 from "../../../assets/images/1.jpeg";
import image2 from "../../../assets/images/2.jpeg";
import image3 from "../../../assets/images/3.jpg";
import image4 from "../../../assets/images/4.jpeg";

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
              transition={{ duration: 0.3, ease: [0.4, 0.0, 0.2, 1] }}
              className="text-gray-500 text-3xl font-light"
            >
              +
            </motion.span>
          </div>
          <AnimatePresence initial={false}>
            {isOpen && (
              <motion.div
                initial={{ opacity: 0, gridTemplateRows: "0fr" }}
                animate={{ opacity: 1, gridTemplateRows: "1fr" }}
                exit={{ opacity: 0, gridTemplateRows: "0fr" }}
                transition={{ 
                  duration: 0.4, 
                  ease: [0.4, 0.0, 0.2, 1],
                  opacity: { duration: 0.3 }
                }}
                className="grid overflow-hidden"
                style={{ willChange: "grid-template-rows, opacity" }}
              >
                <div className="overflow-hidden">
                  <p className="text-gray-500 text-base mt-6 leading-relaxed font-mono">
                    {description}
                  </p>
                </div>
              </motion.div>
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
      title: "You bring scans. We bring expert radiologists.",
      description:
        "Connect your DICOM data from PACS or cloud storage. Our board-certified radiologists handle MRI, CT, X-ray, and pathology slides with domain-specific expertise.",
      image: image1,
    },
    {
      number: "02",
      title: "Clinical-grade precision.",
      description:
        "Define custom annotation schemas for tumor detection, organ segmentation, and anomaly classification. Multi-stage doctor review ensures FDA-ready label quality.",
      image: image2,
    },
    {
      number: "03",
      title: "HIPAA-compliant automation.",
      description:
        "Integrate directly with your secure ML pipeline. Create projects, import de-identified data, and export segmentation masks or structured reports via our Python SDK.",
      image: image3,
    },
    {
      number: "04",
      title: "Compliance built into every pixel.",
      description:
        "PHI redaction, audit logs, and SOC 2 Type II security come standard. Ensure your training data meets the strictest healthcare compliance requirements.",
      image: image4,
    },
  ];

  // Update active feature based on scroll progress with throttling
  useEffect(() => {
    let rafId: number | null = null;
    
    const unsubscribe = scrollYProgress.on("change", (latest) => {
      // Use requestAnimationFrame to throttle updates
      if (rafId !== null) {
        cancelAnimationFrame(rafId);
      }
      
      rafId = requestAnimationFrame(() => {
        const featureCount = features.length;
        const newIndex = Math.min(
          Math.floor(latest * featureCount),
          featureCount - 1
        );
        setActiveIndex((prev) => {
          // Only update if index actually changed
          return prev !== newIndex ? newIndex : prev;
        });
      });
    });

    return () => {
      unsubscribe();
      if (rafId !== null) {
        cancelAnimationFrame(rafId);
      }
    };
  }, [scrollYProgress, features.length]);

  return (
    <div className="relative bg-black">
      {/* Heading section - scrolls normally */}
      <div className="min-h-[20vh] flex items-center">
        <div className="max-w-7xl mx-auto px-6 w-full">
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white leading-tight max-w-2xl">
            Built for Healthcare AI.
            <br />
            Scales with your data.
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
              <div className="relative h-[70vh] hidden lg:block">
                <div className="h-full w-full">
                  <AnimatePresence initial={false}>
                    <motion.div
                      key={activeIndex}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ 
                        duration: 0.5, 
                        ease: [0.4, 0.0, 0.2, 1]
                      }}
                      className="absolute inset-0 w-full h-full"
                      style={{ willChange: "opacity" }}
                    >
                      <img
                        src={features[activeIndex].image}
                        alt={features[activeIndex].title}
                        className="w-full h-full object-cover rounded-lg border border-gray-800"
                        loading="lazy"
                        style={{ transform: "translateZ(0)" }}
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
