/**
 * Watermark Overlay Component
 *
 * Displays dynamic watermark with user info on sensitive content.
 * Watermark is designed to be:
 * - Visible but not obstructive
 * - Randomized position to prevent easy removal
 * - Contains traceable user information
 */

import React, { useMemo } from "react";
import PropTypes from "prop-types";
import "./WatermarkOverlay.scss";

/**
 * Format timestamp for display
 */
const formatTimestamp = (date) => {
  const d = date || new Date();
  return d.toISOString().slice(0, 16).replace("T", " ");
};

/**
 * Mask identifier for privacy
 */
const maskIdentifier = (id) => {
  if (!id || id.length <= 5) return id;
  return `${id.slice(0, 3)}***${id.slice(-2)}`;
};

/**
 * WatermarkOverlay - Displays traceable watermark on content
 *
 * @param {Object} props
 * @param {string} props.userId - User identifier (will be masked)
 * @param {string} props.sessionId - Session identifier
 * @param {string} props.pattern - "tiled", "diagonal", or "corner"
 * @param {number} props.opacity - Watermark opacity (0-1)
 * @param {React.ReactNode} props.children - Content to watermark
 */
const WatermarkOverlay = ({
  userId = "",
  sessionId = "",
  pattern = "diagonal",
  opacity = 0.08,
  fontSize = 12,
  children,
}) => {
  const watermarkText = useMemo(() => {
    const parts = [];
    if (userId) parts.push(maskIdentifier(userId));
    parts.push(formatTimestamp(new Date()));
    if (sessionId) parts.push(sessionId.slice(0, 8));
    return parts.join(" | ");
  }, [userId, sessionId]);

  // Generate random rotation for anti-tampering
  const rotation = useMemo(() => {
    return -15 + Math.random() * 10; // Between -15 and -5 degrees
  }, []);

  const overlayStyle = {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    pointerEvents: "none",
    userSelect: "none",
    WebkitUserSelect: "none",
    overflow: "hidden",
    zIndex: 1000,
  };

  const renderTiledPattern = () => {
    const tiles = [];
    const rows = 10;
    const cols = 6;

    for (let i = 0; i < rows; i++) {
      for (let j = 0; j < cols; j++) {
        tiles.push(
          <div
            key={`${i}-${j}`}
            className="watermark-tile"
            style={{
              position: "absolute",
              top: `${(i / rows) * 100}%`,
              left: `${(j / cols) * 100}%`,
              transform: `rotate(${rotation}deg)`,
              opacity,
              fontSize: `${fontSize}px`,
              color: "#888",
              whiteSpace: "nowrap",
            }}
          >
            {watermarkText}
          </div>
        );
      }
    }
    return tiles;
  };

  const renderDiagonalPattern = () => {
    const tiles = [];
    const count = 15;

    for (let i = 0; i < count; i++) {
      tiles.push(
        <div
          key={i}
          className="watermark-diagonal"
          style={{
            position: "absolute",
            top: `${(i / count) * 120 - 10}%`,
            left: "-5%",
            right: "-5%",
            transform: `rotate(${rotation}deg)`,
            opacity,
            fontSize: `${fontSize}px`,
            color: "#888",
            whiteSpace: "nowrap",
            textAlign: "center",
          }}
        >
          {watermarkText}
        </div>
      );
    }
    return tiles;
  };

  const renderCornerWatermark = () => (
    <div
      className="watermark-corner"
      style={{
        position: "absolute",
        bottom: "10px",
        right: "10px",
        opacity: opacity * 3,
        fontSize: `${fontSize}px`,
        color: "#666",
        background: "rgba(255, 255, 255, 0.7)",
        padding: "2px 6px",
        borderRadius: "3px",
      }}
    >
      {watermarkText}
    </div>
  );

  return (
    <div style={{ position: "relative" }} className="watermark-container">
      {children}
      <div style={overlayStyle} className="watermark-overlay">
        {pattern === "tiled" && renderTiledPattern()}
        {pattern === "diagonal" && renderDiagonalPattern()}
        {pattern === "corner" && renderCornerWatermark()}
      </div>
    </div>
  );
};

WatermarkOverlay.propTypes = {
  userId: PropTypes.string,
  sessionId: PropTypes.string,
  pattern: PropTypes.oneOf(["tiled", "diagonal", "corner"]),
  opacity: PropTypes.number,
  fontSize: PropTypes.number,
  children: PropTypes.node,
};

export default WatermarkOverlay;
