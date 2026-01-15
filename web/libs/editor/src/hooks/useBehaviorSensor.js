/**
 * React Hook for Behavior Sensor
 *
 * Usage:
 *   import useBehaviorSensor from 'hooks/useBehaviorSensor';
 *
 *   function TaskView({ taskId, projectId }) {
 *     useBehaviorSensor({ taskId, projectId });
 *     return <div>...</div>;
 *   }
 */

import { useEffect, useRef } from "react";
import BehaviorSensor from "../utils/behaviorSensor";

/**
 * Hook to initialize and manage behavior sensor
 *
 * @param {Object} options
 * @param {number} options.taskId - Current task ID
 * @param {number} options.projectId - Current project ID
 * @param {boolean} options.enabled - Whether sensor is enabled (default: true)
 * @param {boolean} options.debug - Enable debug logging (default: false)
 */
const useBehaviorSensor = ({
  taskId = null,
  projectId = null,
  enabled = true,
  debug = false,
} = {}) => {
  const sensorRef = useRef(null);

  // Initialize sensor on mount
  useEffect(() => {
    if (!enabled) return;

    // Create sensor instance
    sensorRef.current = new BehaviorSensor({
      enabled: true,
      debug,
    });

    // Cleanup on unmount
    return () => {
      if (sensorRef.current) {
        sensorRef.current.setEnabled(false);
        sensorRef.current = null;
      }
    };
  }, [enabled, debug]);

  // Update context when task/project changes
  useEffect(() => {
    if (sensorRef.current && (taskId || projectId)) {
      sensorRef.current.setContext(taskId, projectId);
    }
  }, [taskId, projectId]);

  // Return sensor instance for direct access if needed
  return sensorRef.current;
};

export default useBehaviorSensor;
