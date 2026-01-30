import { motion, useScroll, useTransform } from "framer-motion";
import { useRef, useEffect, useState } from "react";
import { PrismBackground } from "./PrismBackground";
import { GlitchTextBlock } from "./GlitchText";

export const HeroSection = () => {
  const { scrollY } = useScroll();
  const [scrollValues, setScrollValues] = useState({ y: 0, opacity: 1 });
  const rafRef = useRef<number>();
  
  // Throttle scroll transforms with RAF for better performance
  useEffect(() => {
    const updateScroll = () => {
      const scrollYValue = scrollY.get();
      const newY = Math.min(150, (scrollYValue / 500) * 150);
      const newOpacity = Math.max(0, 1 - (scrollYValue / 400));
      setScrollValues({ y: newY, opacity: newOpacity });
    };
    
    const unsubscribe = scrollY.on("change", () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      rafRef.current = requestAnimationFrame(updateScroll);
    });
    
    return () => {
      unsubscribe();
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [scrollY]);

  return (
    <section 
      className="relative min-h-screen flex items-center justify-center overflow-hidden"
      style={{ 
        opacity: scrollValues.opacity,
        contain: "layout style paint",
        willChange: scrollValues.y > 0 ? "opacity" : "auto",
      }}
    >
      {/* Prism Background - react-bits Prism component */}
      <div 
        className="absolute inset-0 bg-black"
        style={{ 
          contain: "strict",
        }}
      >
        <PrismBackground
          height={3}
          baseWidth={5}
          animationType="hover"
          glow={1}
          noise={0.2}
          transparent
          scale={3.1}
          hueShift={0}
          colorFrequency={1}
          hoverStrength={2}
          inertia={0.05}
          bloom={0.8}
          timeScale={0.4}
          suspendWhenOffscreen={true}
        />
      </div>

      {/* Content - centered like Lambda reference */}
      <div 
        className="relative z-10 w-full max-w-8xl mx-auto px-6 text-center"
        style={{ 
          transform: `translateY(${scrollValues.y}px)`,
          willChange: scrollValues.y > 0 ? "transform" : "auto",
        }}
      >
        {/* Subheading with glitch effect */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="text-gray-300 text-base md:text-lg tracking-normal mb-8 font-medium"
        >
          From raw data to life-saving models, Synapse connects your entire AI lifecycle.
        </motion.p>

        {/* Main heading - matching Lambda size with hover glitch effect */}
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="text-5xl md:text-7xl lg:text-8xl font-bold tracking-normal mb-14 leading-normal"
          style={{ fontFamily: "'Space Grotesk', sans-serif" }}
        >
          <GlitchTextBlock
            lines={["Accelerate Your", "Medical AI"]}
            className="text-white"
          />
        </motion.h1>

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="flex flex-col sm:flex-row gap-4 justify-center"
        >
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="bg-[#e8e4d9] text-black px-10 py-5 text-[13px] font-semibold tracking-[0.2em] transition-colors uppercase hover:bg-[#d8d4c9]"
            style={{ willChange: "transform" }}
          >
            Start Labeling
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="bg-[#8b5cf6] text-white px-10 py-5 text-[13px] font-semibold tracking-[0.2em] transition-colors uppercase hover:bg-[#7c5ce0]"
            style={{ willChange: "transform" }}
          >
            View Python SDK
          </motion.button>
        </motion.div>
      </div>
    
      {/* Right side vertical text */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1, duration: 1 }}
        className="absolute right-6 top-1/2 -translate-y-1/2 hidden lg:block"
      >
        <div className="flex flex-col items-center gap-4">
          <div className="w-px h-20 bg-gradient-to-b from-transparent via-gray-600 to-transparent" />
          <span className="text-gray-500 text-[10px] tracking-[0.3em] [writing-mode:vertical-lr] rotate-180">
            // Expert Medical Review //
          </span>
          <div className="w-px h-20 bg-gradient-to-b from-transparent via-gray-600 to-transparent" />
        </div>
      </motion.div>

    </section>
  );
};
