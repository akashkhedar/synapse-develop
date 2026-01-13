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
      title: "You bring data. We bring expert annotators.",
      description:
        "Connect your S3, GCS, or Azure storage. Our trained annotators handle images, text, audio, and video with domain-specific expertise and quality guarantees.",
      image: "https://wallpapers.com/images/hd/4k-tech-105e3a4x7aw7coqd.jpg",
    },
    {
      number: "02",
      title: "Your labels. Your quality standards.",
      description:
        "Define custom annotation schemas with our visual editor. Set consensus requirements, review workflows, and accuracy thresholds that match your ML pipeline needs.",
      image: "https://cdn.wallpapersafari.com/64/96/9m8BVu.jpg",
    },
    {
      number: "03",
      title: "SDK-first automation.",
      description:
        "Integrate directly with your ML pipeline using our Python SDK. Create projects, import from cloud storage, monitor progress, and export COCO, YOLO, or custom formats programmatically.",
      image:
        "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8aW5mb3JtYXRpb24lMjB0ZWNobm9sb2d5fGVufDB8fDB8fHww",
    },
    {
      number: "04",
      title: "Quality built into every label.",
      description:
        "Multi-annotator consensus, automated agreement scoring, expert reviews, and continuous accuracy monitoring ensure your training data meets production standards.",
      image: "https://wallpapers.com/images/hd/4k-tech-2k2jzc0qemh7y38n.jpg",
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
            Built for ML teams.
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
