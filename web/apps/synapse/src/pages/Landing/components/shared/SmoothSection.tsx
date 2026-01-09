import { motion, useInView } from "framer-motion";
import { useRef } from "react";

interface SmoothSectionProps {
  children: React.ReactNode;
  className?: string;
}

export const SmoothSection = ({ children, className = "" }: SmoothSectionProps) => {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, amount: 0.2 });

  return (
    <motion.section
      ref={ref}
      initial={{ opacity: 0, y: 80 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 80 }}
      transition={{ duration: 0.8, ease: [0.25, 0.1, 0.25, 1] }}
      className={className}
    >
      {children}
    </motion.section>
  );
};
