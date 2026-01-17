import React from "react";
import { motion } from "framer-motion";
import "./LoadingState.css";

interface LoadingStateProps {
  /** Loading message to display */
  message?: string;
  /** Color of the loading dot accent */
  color?: string;
  /** Full screen overlay or inline */
  fullScreen?: boolean;
}

/**
 * Consistent loading state with animated dot and optional message
 */
export const LoadingState: React.FC<LoadingStateProps> = ({
  message = "Loading...",
  color = "#8b5cf6",
  fullScreen = true,
}) => {
  return (
    <div className={`loading-state ${fullScreen ? "loading-state--full" : ""}`}>
      <motion.div
        className="loading-dot"
        style={{ backgroundColor: color }}
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.5, 1, 0.5],
        }}
        transition={{
          duration: 1.5,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      {message && <span className="loading-text">{message}</span>}
    </div>
  );
};

export default LoadingState;
