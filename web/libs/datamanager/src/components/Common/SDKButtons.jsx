import { useSDK } from "../../providers/SDKProvider";
import { Button } from "@synapse/ui";

// Modern toolbar button styles
const toolbarButtonStyle = {
  background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.12), rgba(168, 85, 247, 0.08))',
  border: '1px solid rgba(139, 92, 246, 0.35)',
  color: '#c4b5fd',
  borderRadius: '8px',
  fontWeight: 600,
  fontSize: '12px',
  letterSpacing: '0.04em',
  textTransform: 'uppercase',
  transition: 'all 0.2s ease',
  padding: '0 14px',
};

const SDKButton = ({ eventName, testId, ...props }) => {
  const sdk = useSDK();

  return sdk.hasHandler(eventName) ? (
    <Button
      {...props}
      size={props.size ?? "small"}
      look={props.look ?? "outlined"}
      variant={props.variant ?? "neutral"}
      aria-label={`${eventName.replace("Clicked", "")} button`}
      data-testid={testId}
      style={{
        ...toolbarButtonStyle,
        ...props.style,
      }}
      onClick={() => {
        sdk.invoke(eventName);
      }}
    />
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


