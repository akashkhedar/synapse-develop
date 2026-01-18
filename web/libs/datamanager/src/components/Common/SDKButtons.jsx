import { useState } from "react";
import { useSDK } from "../../providers/SDKProvider";

const SDKButton = ({ eventName, testId, children, ...props }) => {
  const sdk = useSDK();
  const [isHovered, setIsHovered] = useState(false);

  return sdk.hasHandler(eventName) ? (
    <button
      {...props}
      aria-label={`${eventName.replace("Clicked", "")} button`}
      data-testid={testId}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        background: 'black',
        border: `1px solid ${isHovered ? 'rgba(139, 92, 246, 0.5)' : 'rgba(55, 65, 81, 0.5)'}`,
        borderRadius: '10px',
        color: '#c4b5fd',
        fontWeight: 600,
        fontSize: '13px',
        height: '32px',
        padding: '0 14px',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '6px',
        fontFamily: "'Space Grotesk', system-ui, -apple-system, sans-serif",
        outline: 'none',
        transition: 'all 0.15s ease',
        boxShadow: isHovered ? '0 0 12px rgba(139, 92, 246, 0.15)' : 'none',
        ...props.style,
      }}
      onClick={() => {
        sdk.invoke(eventName);
      }}
    >
      {children}
    </button>
  ) : null;
};

export const SettingsButton = ({ ...props }) => {
  return <SDKButton {...props} eventName="settingsClicked" />;
};

export const ImportButton = ({ ...props }) => {
  return <SDKButton {...props} eventName="importClicked" testId="dm-import-button" />;
};

export const ExportButton = ({ ...props }) => {
  return <SDKButton {...props} eventName="exportClicked" testId="dm-export-button" />;
};

