import React from "react";
import { motion } from "framer-motion";
import "./FloatingPixels.css";

interface PixelConfig {
  x: string;
  y: string;
  size: number;
  opacity: number;
}

interface FloatingPixelsProps {
  /** Color of the pixels (defaults to purple #8b5cf6) */
  color?: string;
  /** Custom pixel configurations, uses default if not provided */
  pixels?: PixelConfig[];
}

const DEFAULT_PIXELS: PixelConfig[] = [
  { x: "5%", y: "15%", size: 3, opacity: 0.2 },
  { x: "12%", y: "45%", size: 4, opacity: 0.3 },
  { x: "20%", y: "70%", size: 3, opacity: 0.15 },
  { x: "85%", y: "20%", size: 4, opacity: 0.25 },
  { x: "90%", y: "55%", size: 3, opacity: 0.2 },
  { x: "78%", y: "80%", size: 4, opacity: 0.15 },
];

/**
 * Floating decorative pixels that animate subtly
 * Used as a background decoration on dark-themed pages
 */
export const FloatingPixels: React.FC<FloatingPixelsProps> = ({
  color = "#8b5cf6",
  pixels = DEFAULT_PIXELS,
}) => {
  return (
    <div className="floating-pixels">
      {pixels.map((p, i) => (
        <motion.div
          key={i}
          className="floating-pixel"
          style={{
            left: p.x,
            top: p.y,
            width: p.size,
            height: p.size,
            opacity: p.opacity,
            backgroundColor: color,
          }}
          animate={{
            opacity: [p.opacity * 0.5, p.opacity, p.opacity * 0.5],
            scale: [0.9, 1.1, 0.9],
          }}
          transition={{
            duration: 4 + Math.random() * 2,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  );
};

export default FloatingPixels;
