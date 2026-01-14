/**
 * Screen Capture Detection Hook
 *
 * Detects and prevents various screen capture methods:
 * - Screen sharing API
 * - Browser print
 * - Window blur (potential screenshot indicator)
 */

import { useEffect, useCallback, useRef } from "react";

/**
 * useScreenCaptureDetection - Detects screen capture attempts
 *
 * @param {Object} options
 * @param {Function} options.onScreenShare - Called when screen share is attempted
 * @param {Function} options.onPrintAttempt - Called when print is attempted
 * @param {Function} options.onWindowBlur - Called when window loses focus
 * @param {boolean} options.blockScreenShare - Block getDisplayMedia API
 * @param {boolean} options.blockPrint - Block printing
 * @param {boolean} options.enabled - Enable/disable detection
 */
const useScreenCaptureDetection = ({
  onScreenShare = null,
  onPrintAttempt = null,
  onWindowBlur = null,
  blockScreenShare = true,
  blockPrint = true,
  enabled = true,
} = {}) => {
  const originalGetDisplayMedia = useRef(null);
  const blurCount = useRef(0);
  const lastBlurTime = useRef(0);

  // Handle window blur (potential screenshot)
  const handleBlur = useCallback(() => {
    if (!enabled) return;

    const now = Date.now();

    // Track rapid blur events (might indicate screenshot tool)
    if (now - lastBlurTime.current < 1000) {
      blurCount.current++;
    } else {
      blurCount.current = 1;
    }
    lastBlurTime.current = now;

    if (onWindowBlur) {
      onWindowBlur({
        blurCount: blurCount.current,
        timestamp: now,
      });
    }

    // Log suspicious rapid blur events
    if (blurCount.current >= 3) {
      console.warn(
        "[Security] Rapid window blur detected - possible screenshot activity"
      );
    }
  }, [enabled, onWindowBlur]);

  // Handle before print
  const handleBeforePrint = useCallback(
    (e) => {
      if (!enabled) return;

      if (onPrintAttempt) {
        onPrintAttempt({ event: "before_print" });
      }

      if (blockPrint) {
        console.warn("[Security] Print attempt blocked");
      }
    },
    [enabled, blockPrint, onPrintAttempt]
  );

  // Handle after print
  const handleAfterPrint = useCallback(() => {
    if (!enabled) return;

    if (onPrintAttempt) {
      onPrintAttempt({ event: "after_print" });
    }
  }, [enabled, onPrintAttempt]);

  // Block screen sharing
  useEffect(() => {
    if (!enabled || !blockScreenShare) return;

    if (navigator.mediaDevices?.getDisplayMedia) {
      originalGetDisplayMedia.current = navigator.mediaDevices.getDisplayMedia;

      navigator.mediaDevices.getDisplayMedia = async function (...args) {
        console.warn("[Security] Screen sharing blocked for security");

        if (onScreenShare) {
          onScreenShare({ blocked: true, args });
        }

        throw new DOMException(
          "Screen capture is disabled for security reasons",
          "NotAllowedError"
        );
      };
    }

    return () => {
      // Restore original on cleanup
      if (originalGetDisplayMedia.current && navigator.mediaDevices) {
        navigator.mediaDevices.getDisplayMedia =
          originalGetDisplayMedia.current;
      }
    };
  }, [enabled, blockScreenShare, onScreenShare]);

  // Add event listeners
  useEffect(() => {
    if (!enabled) return;

    window.addEventListener("blur", handleBlur);
    window.addEventListener("beforeprint", handleBeforePrint);
    window.addEventListener("afterprint", handleAfterPrint);

    return () => {
      window.removeEventListener("blur", handleBlur);
      window.removeEventListener("beforeprint", handleBeforePrint);
      window.removeEventListener("afterprint", handleAfterPrint);
    };
  }, [enabled, handleBlur, handleBeforePrint, handleAfterPrint]);

  // Add CSS to block printing
  useEffect(() => {
    if (!enabled || !blockPrint) return;

    const styleId = "security-print-block";
    let style = document.getElementById(styleId);

    if (!style) {
      style = document.createElement("style");
      style.id = styleId;
      style.textContent = `
        @media print {
          body * {
            display: none !important;
            visibility: hidden !important;
          }
          
          body::after {
            content: 'Printing is disabled for security reasons.';
            display: block !important;
            visibility: visible !important;
            text-align: center;
            padding: 50px;
            font-size: 24px;
            color: #333;
          }
        }
      `;
      document.head.appendChild(style);
    }

    return () => {
      const styleToRemove = document.getElementById(styleId);
      if (styleToRemove) {
        styleToRemove.remove();
      }
    };
  }, [enabled, blockPrint]);

  return {
    blurCount: blurCount.current,
  };
};

export default useScreenCaptureDetection;
