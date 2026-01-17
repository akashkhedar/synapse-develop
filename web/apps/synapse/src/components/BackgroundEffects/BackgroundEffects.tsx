import React from "react";
import "./BackgroundEffects.css";

interface BackgroundGridProps {
  /** Line color opacity (0-1) */
  opacity?: number;
  /** Grid size in pixels */
  size?: number;
}

/**
 * Subtle grid pattern background effect
 */
export const BackgroundGrid: React.FC<BackgroundGridProps> = ({
  opacity = 0.03,
  size = 60,
}) => {
  return (
    <div
      className="bg-grid"
      style={{
        backgroundImage: `
          linear-gradient(rgba(255, 255, 255, ${opacity}) 1px, transparent 1px),
          linear-gradient(90deg, rgba(255, 255, 255, ${opacity}) 1px, transparent 1px)
        `,
        backgroundSize: `${size}px ${size}px`,
      }}
    />
  );
};

interface BackgroundGlowProps {
  /** Glow color in hex or rgba */
  color?: string;
  /** Position: 'top-right' | 'top-left' | 'center' */
  position?: "top-right" | "top-left" | "center";
  /** Size in pixels */
  size?: number;
}

/**
 * Radial gradient glow effect for backgrounds
 */
export const BackgroundGlow: React.FC<BackgroundGlowProps> = ({
  color = "rgba(139, 92, 246, 0.08)",
  position = "top-right",
  size = 600,
}) => {
  const getPositionStyles = () => {
    switch (position) {
      case "top-left":
        return { top: 0, left: 0 };
      case "center":
        return { top: "50%", left: "50%", transform: "translate(-50%, -50%)" };
      case "top-right":
      default:
        return { top: 0, right: 0 };
    }
  };

  return (
    <div
      className="bg-glow"
      style={{
        ...getPositionStyles(),
        width: size,
        height: size,
        background: `radial-gradient(ellipse at center, ${color} 0%, transparent 70%)`,
      }}
    />
  );
};
