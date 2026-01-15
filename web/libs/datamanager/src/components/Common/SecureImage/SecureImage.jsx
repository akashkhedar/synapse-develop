import React, { useEffect, useRef, useState } from "react";

/**
 * Secure the canvas element to prevent data extraction
 */
const secureCanvas = (canvas) => {
  if (!canvas) return;

  // Override toDataURL to prevent image extraction
  canvas.toDataURL = () => {
    console.warn("Image export is disabled for security reasons");
    return "";
  };

  // Override toBlob to prevent image extraction
  canvas.toBlob = () => {
    console.warn("Image export is disabled for security reasons");
  };

  // Prevent getImageData on the canvas context
  const ctx = canvas.getContext("2d");
  if (ctx) {
    ctx.getImageData = () => {
      console.warn("Image data extraction is disabled for security reasons");
      return new ImageData(1, 1);
    };
  }
};

/**
 * SecureImage component that renders images to canvas
 * Prevents right-click, drag, and data extraction methods
 *
 * @param {Object} props
 * @param {string} props.src - Image source URL
 * @param {string} [props.alt] - Alt text (not displayed, for accessibility)
 * @param {string|number} [props.width] - Width of the image
 * @param {string|number} [props.height] - Height of the image
 * @param {Object} [props.style] - Additional styles
 * @param {string} [props.className] - Additional CSS classes
 * @param {string} [props.crossOrigin] - Cross-origin setting for image
 */
export const SecureImage = ({
  src,
  alt,
  width,
  height,
  style = {},
  className = "",
  crossOrigin = "anonymous",
  ...rest
}) => {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    if (!src) return;

    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const img = new Image();
    if (crossOrigin) {
      img.crossOrigin = crossOrigin;
    }

    img.onload = () => {
      try {
        // Determine canvas dimensions
        let canvasWidth = img.naturalWidth;
        let canvasHeight = img.naturalHeight;

        // If explicit dimensions are provided, scale to fit
        const targetWidth =
          typeof width === "number" ? width : parseInt(width, 10) || 0;
        const targetHeight =
          typeof height === "number" ? height : parseInt(height, 10) || 0;

        if (targetWidth || targetHeight) {
          if (targetWidth && targetHeight) {
            // Both dimensions specified - use object-fit: contain behavior
            const scaleX = targetWidth / img.naturalWidth;
            const scaleY = targetHeight / img.naturalHeight;
            const scale = Math.min(scaleX, scaleY);
            canvasWidth = img.naturalWidth * scale;
            canvasHeight = img.naturalHeight * scale;
          } else if (targetWidth) {
            // Only width specified - maintain aspect ratio
            const scale = targetWidth / img.naturalWidth;
            canvasWidth = targetWidth;
            canvasHeight = img.naturalHeight * scale;
          } else if (targetHeight) {
            // Only height specified - maintain aspect ratio
            const scale = targetHeight / img.naturalHeight;
            canvasHeight = targetHeight;
            canvasWidth = img.naturalWidth * scale;
          }
        }

        canvas.width = canvasWidth;
        canvas.height = canvasHeight;

        const ctx = canvas.getContext("2d");
        if (ctx) {
          ctx.clearRect(0, 0, canvasWidth, canvasHeight);
          ctx.drawImage(img, 0, 0, canvasWidth, canvasHeight);
        }

        // Secure the canvas after rendering
        secureCanvas(canvas);
        setDimensions({ width: canvasWidth, height: canvasHeight });
        setLoaded(true);
        setError(false);
      } catch (err) {
        console.error("Failed to render secure image:", err);
        setError(true);
      }
    };

    img.onerror = () => {
      console.error("Failed to load image:", src);
      setError(true);
      setLoaded(false);
    };

    // Reset state for new image
    setLoaded(false);
    setError(false);
    img.src = src;

    return () => {
      img.onload = null;
      img.onerror = null;
    };
  }, [src, width, height, crossOrigin]);

  // Security event handlers
  const handleContextMenu = (e) => {
    e.preventDefault();
    e.stopPropagation();
    return false;
  };

  const handleDragStart = (e) => {
    e.preventDefault();
    e.stopPropagation();
    return false;
  };

  const handleCopy = (e) => {
    e.preventDefault();
    e.stopPropagation();
    return false;
  };

  // Container style that handles width="auto" or percentage widths
  const containerStyle = {
    display: "inline-block",
    position: "relative",
    userSelect: "none",
    WebkitUserSelect: "none",
    MozUserSelect: "none",
    msUserSelect: "none",
    ...style,
  };

  // Canvas style
  const canvasStyle = {
    display: "block",
    maxWidth: "100%",
    pointerEvents: "none", // Let container handle events
  };

  // Apply width/height to container if using "auto" or percentage
  if (width === "auto" || (typeof width === "string" && width.includes("%"))) {
    containerStyle.width = width;
  }
  if (height && typeof height !== "number") {
    containerStyle.height = height;
  }

  return (
    <div
      ref={containerRef}
      className={className}
      style={containerStyle}
      onContextMenu={handleContextMenu}
      onDragStart={handleDragStart}
      onCopy={handleCopy}
      {...rest}
    >
      <canvas
        ref={canvasRef}
        style={canvasStyle}
        aria-label={alt || "Secure image"}
      />
      {!loaded && !error && (
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            backgroundColor: "rgba(0, 0, 0, 0.1)",
          }}
        >
          Loading...
        </div>
      )}
      {error && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: width || "100px",
            height: height || "100px",
            backgroundColor: "rgba(0, 0, 0, 0.1)",
            color: "var(--text-secondary, #666)",
            fontSize: "12px",
          }}
        >
          Failed to load
        </div>
      )}
    </div>
  );
};

export default SecureImage;
