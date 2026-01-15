import React from "react";
import BehaviorSensor from "../../utils/behaviorSensor";

export interface BehaviorSensorProviderProps {
  children: React.ReactNode;
  taskId?: string | number | null;
  projectId?: string | number | null;
  enabled?: boolean;
  debug?: boolean;
}

export declare const BehaviorSensorProvider: React.FC<BehaviorSensorProviderProps>;

export declare const useBehaviorSensorContext: () => BehaviorSensor | null;

export interface BehaviorSensorTaskContextProps {
  taskId?: string | number | null;
  projectId?: string | number | null;
}

export declare const BehaviorSensorTaskContext: React.FC<BehaviorSensorTaskContextProps>;

export default BehaviorSensorProvider;
