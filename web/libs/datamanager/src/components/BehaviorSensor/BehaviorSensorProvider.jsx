/**
 * BehaviorSensorProvider
 *
 * A wrapper component that initializes the behavior sensor for
 * all child components. Place this at the root of your app or
 * around the data manager interface.
 */

import React, { useEffect, useRef, createContext, useContext } from "react";
import BehaviorSensor from "../../utils/behaviorSensor";

// Context to share the sensor instance
const BehaviorSensorContext = createContext(null);

/**
 * Provider component that initializes and manages the behavior sensor
 */
export const BehaviorSensorProvider = ({
  children,
  taskId = null,
  projectId = null,
  enabled = true,
  debug = false,
}) => {
  const sensorRef = useRef(null);

  // Initialize sensor on mount
  useEffect(() => {
    if (!enabled) return;

    // Only initialize in browser environment
    if (typeof window === "undefined") return;

    sensorRef.current = new BehaviorSensor({
      enabled: true,
      debug,
      endpoint: "/api/telemetry",
      batchInterval: 5000,
    });

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

  return (
    <BehaviorSensorContext.Provider value={sensorRef.current}>
      {children}
    </BehaviorSensorContext.Provider>
  );
};

/**
 * Hook to access the behavior sensor from any child component
 */
export const useBehaviorSensorContext = () => {
  return useContext(BehaviorSensorContext);
};

/**
 * Component that updates the sensor context when task changes
 * Use this inside components that know the current task
 */
export const BehaviorSensorTaskContext = ({ taskId, projectId }) => {
  const sensor = useBehaviorSensorContext();

  useEffect(() => {
    if (sensor && (taskId || projectId)) {
      sensor.setContext(taskId, projectId);
    }
  }, [sensor, taskId, projectId]);

  return null; // This component renders nothing
};

export default BehaviorSensorProvider;
