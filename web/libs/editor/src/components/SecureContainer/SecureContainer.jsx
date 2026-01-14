/**
 * Secure Container Component
 *
 * Wraps content with security measures:
 * - Prevents right-click context menu
 * - Blocks keyboard shortcuts (Ctrl+S, F12, etc.)
 * - Disables text selection and drag
 * - Blocks copy/paste on sensitive content
 */

import React, { useEffect, useCallback } from "react";
import PropTypes from "prop-types";

const BLOCKED_KEY_COMBOS = [
  { ctrl: true, key: "s" }, // Save
  { ctrl: true, shift: true, key: "i" }, // Dev tools
  { ctrl: true, shift: true, key: "j" }, // Dev tools
  { ctrl: true, shift: true, key: "c" }, // Inspect element
  { ctrl: true, key: "u" }, // View source
  { key: "F12" }, // Dev tools
  { ctrl: true, key: "p" }, // Print
];

/**
 * SecureContainer - Prevents common data extraction methods
 *
 * @param {Object} props
 * @param {React.ReactNode} props.children - Content to protect
 * @param {boolean} props.blockRightClick - Block context menu (default: true)
 * @param {boolean} props.blockKeyboard - Block keyboard shortcuts (default: true)
 * @param {boolean} props.blockDrag - Block drag operations (default: true)
 * @param {boolean} props.blockSelection - Block text selection (default: false)
 * @param {boolean} props.blockCopy - Block copy operations (default: true)
 * @param {Function} props.onSecurityEvent - Callback for security events
 */
const SecureContainer = ({
  children,
  blockRightClick = true,
  blockKeyboard = true,
  blockDrag = true,
  blockSelection = false,
  blockCopy = true,
  onSecurityEvent = null,
}) => {
  const logSecurityEvent = useCallback(
    (eventType, details = {}) => {
      console.warn(`[Security] ${eventType}`, details);
      if (onSecurityEvent) {
        onSecurityEvent(eventType, details);
      }
    },
    [onSecurityEvent]
  );

  // Block context menu (right-click)
  const handleContextMenu = useCallback(
    (e) => {
      if (blockRightClick) {
        e.preventDefault();
        logSecurityEvent("context_menu_blocked");
        return false;
      }
    },
    [blockRightClick, logSecurityEvent]
  );

  // Block drag operations
  const handleDragStart = useCallback(
    (e) => {
      if (blockDrag) {
        e.preventDefault();
        logSecurityEvent("drag_blocked");
        return false;
      }
    },
    [blockDrag, logSecurityEvent]
  );

  // Block copy operations
  const handleCopy = useCallback(
    (e) => {
      if (blockCopy) {
        e.preventDefault();
        logSecurityEvent("copy_blocked");
        return false;
      }
    },
    [blockCopy, logSecurityEvent]
  );

  // Block keyboard shortcuts
  const handleKeyDown = useCallback(
    (e) => {
      if (!blockKeyboard) return;

      const isBlocked = BLOCKED_KEY_COMBOS.some((combo) => {
        const ctrlMatch = combo.ctrl ? e.ctrlKey || e.metaKey : true;
        const shiftMatch = combo.shift
          ? e.shiftKey
          : !combo.shift || !e.shiftKey;
        const keyMatch =
          e.key.toLowerCase() === combo.key.toLowerCase() ||
          e.key === combo.key;

        return (
          ctrlMatch &&
          shiftMatch &&
          keyMatch &&
          (combo.ctrl || combo.shift || combo.key.startsWith("F"))
        );
      });

      if (isBlocked) {
        e.preventDefault();
        e.stopPropagation();
        logSecurityEvent("keyboard_shortcut_blocked", {
          key: e.key,
          ctrl: e.ctrlKey,
        });
        return false;
      }
    },
    [blockKeyboard, logSecurityEvent]
  );

  // Attach global listeners
  useEffect(() => {
    document.addEventListener("contextmenu", handleContextMenu);
    document.addEventListener("dragstart", handleDragStart);
    document.addEventListener("keydown", handleKeyDown);
    document.addEventListener("copy", handleCopy);

    return () => {
      document.removeEventListener("contextmenu", handleContextMenu);
      document.removeEventListener("dragstart", handleDragStart);
      document.removeEventListener("keydown", handleKeyDown);
      document.removeEventListener("copy", handleCopy);
    };
  }, [handleContextMenu, handleDragStart, handleKeyDown, handleCopy]);

  const containerStyle = {
    userSelect: blockSelection ? "none" : "auto",
    WebkitUserSelect: blockSelection ? "none" : "auto",
    MozUserSelect: blockSelection ? "none" : "auto",
    msUserSelect: blockSelection ? "none" : "auto",
    WebkitTouchCallout: blockSelection ? "none" : "auto",
  };

  return (
    <div
      style={containerStyle}
      onContextMenu={handleContextMenu}
      onDragStart={handleDragStart}
      onCopy={handleCopy}
    >
      {children}
    </div>
  );
};

SecureContainer.propTypes = {
  children: PropTypes.node.isRequired,
  blockRightClick: PropTypes.bool,
  blockKeyboard: PropTypes.bool,
  blockDrag: PropTypes.bool,
  blockSelection: PropTypes.bool,
  blockCopy: PropTypes.bool,
  onSecurityEvent: PropTypes.func,
};

export default SecureContainer;
