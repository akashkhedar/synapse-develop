export interface BehaviorSensorOptions {
  endpoint?: string;
  batchInterval?: number;
  maxBatchSize?: number;
  enabled?: boolean;
  debug?: boolean;
}

declare class BehaviorSensor {
  constructor(options?: BehaviorSensorOptions);

  /**
   * Set current task context
   */
  setContext(
    taskId: string | number | null,
    projectId: string | number | null
  ): void;

  /**
   * Enable/disable the sensor
   */
  setEnabled(enabled: boolean): void;
}

export default BehaviorSensor;
