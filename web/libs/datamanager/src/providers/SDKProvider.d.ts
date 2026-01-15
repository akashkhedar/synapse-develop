import React from "react";

export declare const SDKContext: React.Context<any>;

export interface SDKProviderProps {
  sdk: any;
  children: React.ReactNode;
}

export declare const SDKProvider: React.FC<SDKProviderProps>;

export declare const useSDK: () => any;
