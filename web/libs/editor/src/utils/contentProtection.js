/**
 * Content Protection Utilities
 *
 * Provides DRM-style content protection for sensitive media:
 * - Canvas protection (disable toDataURL/toBlob)
 * - DevTools detection
 * - Clipboard blocking
 * - Visibility change detection
 */

/**
 * Secure a canvas element by overriding extraction methods
 *
 * @param {HTMLCanvasElement} canvas - Canvas to protect
 * @param {boolean} allowInternalExport - Allow exports from trusted code
 */
export const secureCanvas = (canvas, allowInternalExport = false) => {
  if (!canvas || !(canvas instanceof HTMLCanvasElement)) {
    console.warn("[Security] secureCanvas: Invalid canvas element");
    return;
  }

  const originalToDataURL = canvas.toDataURL.bind(canvas);
  const originalToBlob = canvas.toBlob.bind(canvas);
  const originalGetImageData = null;

  // Override toDataURL
  canvas.toDataURL = function (...args) {
    if (allowInternalExport && this._securityBypass) {
      return originalToDataURL(...args);
    }
    console.warn("[Security] Canvas toDataURL blocked");
    return "data:image/png;base64,";
  };

  // Override toBlob
  canvas.toBlob = function (callback, ...args) {
    if (allowInternalExport && this._securityBypass) {
      return originalToBlob(callback, ...args);
    }
    console.warn("[Security] Canvas toBlob blocked");
    if (callback) {
      callback(null);
    }
  };

  // Store originals for internal use
  canvas._originalToDataURL = originalToDataURL;
  canvas._originalToBlob = originalToBlob;

  return canvas;
};

/**
 * Detect DevTools open state
 * Uses various heuristics to detect if developer tools are open
 *
 * @param {Function} onDetected - Callback when DevTools detected
 * @returns {Function} Cleanup function
 */
export const detectDevTools = (onDetected) => {
  let isOpen = false;
  const threshold = 160;

  const check = () => {
    const widthDiff = window.outerWidth - window.innerWidth > threshold;
    const heightDiff = window.outerHeight - window.innerHeight > threshold;

    if ((widthDiff || heightDiff) && !isOpen) {
      isOpen = true;
      if (onDetected) {
        onDetected({ detected: true, method: "dimension" });
      }
    } else if (!widthDiff && !heightDiff) {
      isOpen = false;
    }
  };

  // Check on resize
  window.addEventListener("resize", check);

  // Initial check
  check();

  // Cleanup function
  return () => {
    window.removeEventListener("resize", check);
  };
};

/**
 * Block clipboard operations
 *
 * @param {HTMLElement} element - Element to protect
 * @param {Object} options - Options
 * @returns {Function} Cleanup function
 */
export const blockClipboard = (element, options = {}) => {
  const { blockCopy = true, blockCut = true, blockPaste = false } = options;

  const handlers = {};

  if (blockCopy) {
    handlers.copy = (e) => {
      e.preventDefault();
      console.warn("[Security] Copy operation blocked");
    };
    element.addEventListener("copy", handlers.copy);
  }

  if (blockCut) {
    handlers.cut = (e) => {
      e.preventDefault();
      console.warn("[Security] Cut operation blocked");
    };
    element.addEventListener("cut", handlers.cut);
  }

  if (blockPaste) {
    handlers.paste = (e) => {
      e.preventDefault();
      console.warn("[Security] Paste operation blocked");
    };
    element.addEventListener("paste", handlers.paste);
  }

  // Cleanup function
  return () => {
    Object.entries(handlers).forEach(([event, handler]) => {
      element.removeEventListener(event, handler);
    });
  };
};

/**
 * Detect visibility changes (tab switches, minimizing)
 *
 * @param {Function} onHidden - Called when page becomes hidden
 * @param {Function} onVisible - Called when page becomes visible
 * @returns {Function} Cleanup function
 */
export const detectVisibilityChange = (onHidden, onVisible) => {
  const handleVisibilityChange = () => {
    if (document.hidden) {
      if (onHidden) {
        onHidden({ timestamp: Date.now() });
      }
    } else {
      if (onVisible) {
        onVisible({ timestamp: Date.now() });
      }
    }
  };

  document.addEventListener("visibilitychange", handleVisibilityChange);

  return () => {
    document.removeEventListener("visibilitychange", handleVisibilityChange);
  };
};

/**
 * Apply all content protection measures
 *
 * @param {Object} options
 * @returns {Function} Cleanup function
 */
export const enableContentProtection = (options = {}) => {
  const {
    blockDevTools = true,
    blockPrint = true,
    onSecurityEvent = console.warn,
  } = options;

  const cleanups = [];

  // Block printing via CSS
  if (blockPrint) {
    const style = document.createElement("style");
    style.id = "content-protection-print";
    style.textContent = `
      @media print {
        body {
          display: none !important;
        }
      }
    `;
    document.head.appendChild(style);

    cleanups.push(() => style.remove());
  }

  // Detect DevTools
  if (blockDevTools) {
    cleanups.push(
      detectDevTools((data) => {
        onSecurityEvent("[Security] DevTools detected", data);
      })
    );
  }

  // Detect visibility changes
  cleanups.push(
    detectVisibilityChange(
      () => onSecurityEvent("[Security] Page hidden"),
      () => onSecurityEvent("[Security] Page visible")
    )
  );

  // Return cleanup function
  return () => {
    cleanups.forEach((cleanup) => {
      if (typeof cleanup === "function") {
        cleanup();
      }
    });
  };
};

export default {
  secureCanvas,
  detectDevTools,
  blockClipboard,
  detectVisibilityChange,
  enableContentProtection,
};
