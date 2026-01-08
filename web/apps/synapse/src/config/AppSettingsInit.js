/**
 * Initialize APP_SETTINGS global object
 * This must be imported before any other modules that depend on APP_SETTINGS
 */

// Initialize APP_SETTINGS if not already defined by backend
if (typeof window !== "undefined" && !window.APP_SETTINGS) {
  window.APP_SETTINGS = {
    user: null,
    hostname: window.location.origin,
    feature_flags: {},
    feature_flags_default_value: false,
    billing: {
      enterprise: false,
    },
  };
}

// Make APP_SETTINGS available as a global for backwards compatibility
if (typeof window !== "undefined") {
  window.APP_SETTINGS = window.APP_SETTINGS || {};
  // Export for ES6 modules
  globalThis.APP_SETTINGS = window.APP_SETTINGS;
}

export default typeof window !== "undefined" ? window.APP_SETTINGS : {};

