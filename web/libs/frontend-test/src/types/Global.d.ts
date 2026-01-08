export type {};
declare global {
  interface Window {
    APP_SETTINGS: Record<string, any>;
    FEATURE_FLAGS: Record<string, boolean>;
    SF_CONFIG: Record<any, any>;
    DEFAULT_SF_INIT: boolean;
    Synapse: any;
    Htx: any;
  }
}

