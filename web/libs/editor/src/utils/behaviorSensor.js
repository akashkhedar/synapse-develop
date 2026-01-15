/**
 * Behavior Sensor - Client-Side Telemetry Collection
 *
 * Lightweight module that collects user behavior signals and sends them
 * to /api/telemetry for analysis.
 *
 * Signals collected:
 * - Mouse movement patterns
 * - Click/scroll/zoom frequency
 * - Image dwell time
 * - Tab focus/blur events
 * - DevTools detection
 * - Copy/print screen attempts
 * - VM/RDP indicators
 * - Headless browser detection
 */

class BehaviorSensor {
  constructor(options = {}) {
    this.options = {
      endpoint: "/api/telemetry",
      batchInterval: 5000, // Send every 5 seconds
      maxBatchSize: 20,
      enabled: true,
      debug: false,
      ...options,
    };

    this.events = [];
    this.sessionId = this._generateSessionId();
    this.currentTaskId = null;
    this.currentProjectId = null;
    this.lastImageViewTime = null;
    this.isDevToolsOpen = false;

    // Track for entropy calculation
    this.mousePositions = [];
    this.lastMouseTime = 0;

    if (this.options.enabled) {
      this._init();
    }
  }

  /**
   * Initialize all event listeners
   */
  _init() {
    this._log("BehaviorSensor initializing...");

    // Session start
    this._recordEvent("session_start", {});

    // Mouse tracking
    this._initMouseTracking();

    // Click/scroll/zoom tracking
    this._initInteractionTracking();

    // Tab focus/blur
    this._initFocusTracking();

    // Security events
    this._initSecurityTracking();

    // Environment detection
    this._detectEnvironment();

    // Start batch sender
    this._startBatchSender();

    // Cleanup on page unload
    window.addEventListener("beforeunload", () => {
      this._recordEvent("session_end", {});
      this._sendBatch(true); // Force send
    });

    this._log("BehaviorSensor initialized");
  }

  /**
   * Set current task context
   */
  setContext(taskId, projectId) {
    if (this.currentTaskId !== taskId) {
      // Record dwell time for previous task
      if (this.currentTaskId && this.lastImageViewTime) {
        const dwellMs = Date.now() - this.lastImageViewTime;
        this._recordEvent("dwell", {
          task_id: this.currentTaskId,
          duration_ms: dwellMs,
        });
      }

      this.currentTaskId = taskId;
      this.lastImageViewTime = Date.now();
    }
    this.currentProjectId = projectId;
  }

  /**
   * Mouse movement tracking for entropy calculation
   */
  _initMouseTracking() {
    let moveCount = 0;

    document.addEventListener("mousemove", (e) => {
      moveCount++;

      // Sample every 10th movement
      if (moveCount % 10 === 0) {
        this.mousePositions.push({
          x: e.clientX,
          y: e.clientY,
          t: Date.now(),
        });

        // Keep last 100 positions
        if (this.mousePositions.length > 100) {
          this.mousePositions.shift();
        }

        // Calculate entropy periodically
        if (this.mousePositions.length >= 50 && moveCount % 50 === 0) {
          const entropy = this._calculateMouseEntropy();
          if (entropy < 0.5) {
            // Very low entropy = possibly automated
            this._recordEvent("mouse_entropy", { entropy, suspicious: true });
          }
        }
      }
    });
  }

  /**
   * Calculate mouse movement entropy (randomness)
   * Low entropy = suspicious (automated or unusual patterns)
   */
  _calculateMouseEntropy() {
    if (this.mousePositions.length < 20) return 1;

    const positions = this.mousePositions.slice(-50);
    const deltas = [];

    for (let i = 1; i < positions.length; i++) {
      const dx = positions[i].x - positions[i - 1].x;
      const dy = positions[i].y - positions[i - 1].y;
      const dt = positions[i].t - positions[i - 1].t;

      // Angle of movement
      const angle = Math.atan2(dy, dx);
      deltas.push(angle);
    }

    // Calculate variance as a proxy for entropy
    const mean = deltas.reduce((a, b) => a + b, 0) / deltas.length;
    const variance =
      deltas.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / deltas.length;

    // Normalize to 0-1
    return Math.min(1, variance / Math.PI);
  }

  /**
   * Track clicks, scrolls, and zooms
   */
  _initInteractionTracking() {
    // Click tracking
    document.addEventListener("click", () => {
      this._recordEvent("click", {});
    });

    // Scroll tracking (throttled)
    let lastScrollTime = 0;
    document.addEventListener("scroll", () => {
      const now = Date.now();
      if (now - lastScrollTime > 500) {
        this._recordEvent("scroll", {
          y: window.scrollY,
          height: document.body.scrollHeight,
        });
        lastScrollTime = now;
      }
    });

    // Zoom tracking (wheel with ctrl)
    document.addEventListener("wheel", (e) => {
      if (e.ctrlKey) {
        this._recordEvent("zoom", {
          delta: e.deltaY,
          direction: e.deltaY > 0 ? "out" : "in",
        });
      }
    });
  }

  /**
   * Track tab focus/blur
   */
  _initFocusTracking() {
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        this._recordEvent("blur", {});
      } else {
        this._recordEvent("focus", {});
      }
    });

    window.addEventListener("blur", () => {
      this._recordEvent("blur", { window: true });
    });

    window.addEventListener("focus", () => {
      this._recordEvent("focus", { window: true });
    });
  }

  /**
   * Track security-related events
   */
  _initSecurityTracking() {
    // DevTools detection
    this._detectDevTools();

    // Copy attempt
    document.addEventListener("copy", (e) => {
      this._recordEvent("copy", {});
    });

    // Context menu (right-click)
    document.addEventListener("contextmenu", (e) => {
      this._recordEvent("contextmenu", {
        target: e.target.tagName,
      });
    });

    // Drag attempt
    document.addEventListener("dragstart", (e) => {
      this._recordEvent("dragstart", {
        target: e.target.tagName,
      });
    });

    // Print screen and other shortcuts
    document.addEventListener("keydown", (e) => {
      // Print screen
      if (e.key === "PrintScreen") {
        this._recordEvent("printscreen", {});
      }

      // Ctrl+S (save)
      if (e.ctrlKey && e.key === "s") {
        this._recordEvent("keyboard_shortcut", { keys: "Ctrl+S" });
      }

      // Ctrl+P (print)
      if (e.ctrlKey && e.key === "p") {
        this._recordEvent("keyboard_shortcut", { keys: "Ctrl+P" });
      }

      // F12 (DevTools)
      if (e.key === "F12") {
        this._recordEvent("keyboard_shortcut", { keys: "F12" });
      }
    });
  }

  /**
   * Detect DevTools open
   */
  _detectDevTools() {
    const threshold = 160;

    const check = () => {
      const widthThreshold = window.outerWidth - window.innerWidth > threshold;
      const heightThreshold =
        window.outerHeight - window.innerHeight > threshold;

      const isOpen = widthThreshold || heightThreshold;

      if (isOpen && !this.isDevToolsOpen) {
        this.isDevToolsOpen = true;
        this._recordEvent("devtools", { opened: true });
      } else if (!isOpen && this.isDevToolsOpen) {
        this.isDevToolsOpen = false;
        this._recordEvent("devtools", { opened: false });
      }
    };

    // Check periodically
    setInterval(check, 1000);

    // Also detect via debugger timing
    const detectDebugger = () => {
      const start = performance.now();
      // Debugger statement causes delay when DevTools is open
      // eslint-disable-next-line no-debugger
      debugger;
      const duration = performance.now() - start;

      if (duration > 100) {
        this._recordEvent("devtools", {
          detected: "debugger",
          delay: duration,
        });
      }
    };

    // Run debugger check less frequently to avoid annoyance
    // setInterval(detectDebugger, 30000);
  }

  /**
   * Detect VM, RDP, and other environment indicators
   */
  _detectEnvironment() {
    // Check for headless browser
    const isHeadless = this._detectHeadless();
    if (isHeadless) {
      this._recordEvent("headless", { indicators: isHeadless });
    }

    // Check for VM/RDP indicators
    const vmIndicators = this._detectVM();
    if (vmIndicators.length > 0) {
      this._recordEvent("vm_detected", { indicators: vmIndicators });
    }

    // Check for multiple monitors
    if (window.screen.availWidth > window.screen.width * 1.5) {
      this._recordEvent("multi_monitor", {
        screenWidth: window.screen.width,
        availWidth: window.screen.availWidth,
      });
    }
  }

  /**
   * Detect headless browser
   */
  _detectHeadless() {
    const indicators = [];

    // Check webdriver
    if (navigator.webdriver) {
      indicators.push("webdriver");
    }

    // Check for missing plugins
    if (navigator.plugins.length === 0) {
      indicators.push("no_plugins");
    }

    // Check for missing languages
    if (!navigator.languages || navigator.languages.length === 0) {
      indicators.push("no_languages");
    }

    // Check user agent for headless
    if (/HeadlessChrome|PhantomJS|Selenium/i.test(navigator.userAgent)) {
      indicators.push("user_agent");
    }

    // Check for Puppeteer/Playwright
    if (window.chrome && !window.chrome.runtime) {
      indicators.push("automation_chrome");
    }

    return indicators.length > 0 ? indicators : null;
  }

  /**
   * Detect VM/RDP environment
   */
  _detectVM() {
    const indicators = [];

    // Check screen dimensions (common VM sizes)
    const vmSizes = [
      [800, 600],
      [1024, 768],
      [1280, 1024],
      [1920, 1080],
    ];
    const exact = vmSizes.some(
      ([w, h]) => window.screen.width === w && window.screen.height === h
    );

    // Check for specific VM-related strings
    const ua = navigator.userAgent.toLowerCase();
    if (/vmware|virtualbox|qemu|xen/i.test(navigator.platform)) {
      indicators.push("platform");
    }

    // Check device memory (VMs often have round numbers)
    if (navigator.deviceMemory && [2, 4, 8].includes(navigator.deviceMemory)) {
      // Could be VM, but also could be real - just note it
    }

    // Check hardware concurrency
    if (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 2) {
      indicators.push("low_cpu");
    }

    return indicators;
  }

  /**
   * Record an event
   */
  _recordEvent(type, value) {
    const event = {
      type,
      value,
      timestamp: Math.floor(Date.now() / 1000),
      task_id: this.currentTaskId,
      project_id: this.currentProjectId,
    };

    this.events.push(event);
    this._log(`Event: ${type}`, value);

    // Send immediately if batch is full
    if (this.events.length >= this.options.maxBatchSize) {
      this._sendBatch();
    }
  }

  /**
   * Start the batch sender interval
   */
  _startBatchSender() {
    setInterval(() => {
      this._sendBatch();
    }, this.options.batchInterval);
  }

  /**
   * Send events batch to server
   */
  async _sendBatch(force = false) {
    if (this.events.length === 0) return;

    const eventsToSend = this.events.splice(0, this.options.maxBatchSize);

    try {
      const response = await fetch(this.options.endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include", // Include cookies for auth
        body: JSON.stringify({ events: eventsToSend }),
        keepalive: force, // Keep connection alive for beforeunload
      });

      if (!response.ok) {
        this._log("Failed to send telemetry:", response.status);
        // Put events back for retry
        this.events.unshift(...eventsToSend);
      } else {
        this._log(`Sent ${eventsToSend.length} events`);
      }
    } catch (error) {
      this._log("Error sending telemetry:", error);
      // Put events back for retry
      this.events.unshift(...eventsToSend);
    }
  }

  /**
   * Generate a session ID
   */
  _generateSessionId() {
    return "bs_" + Math.random().toString(36).substring(2, 15);
  }

  /**
   * Debug logging
   */
  _log(...args) {
    if (this.options.debug) {
      console.log("[BehaviorSensor]", ...args);
    }
  }

  /**
   * Enable/disable the sensor
   */
  setEnabled(enabled) {
    this.options.enabled = enabled;
  }
}

// Export for use
export default BehaviorSensor;

// Also attach to window for non-module usage
if (typeof window !== "undefined") {
  window.BehaviorSensor = BehaviorSensor;
}
