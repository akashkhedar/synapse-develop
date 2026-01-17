import { useSDK } from "../../providers/SDKProvider";
import { Button } from "@synapse/ui";

// Modern toolbar button styles
const toolbarButtonStyle = {
  background: 'black',
  border: '1px solid rgba(55, 65, 81, 0.5)',
  color: '#c4b5fd',
  borderRadius: '10px',
  fontWeight: 600,
  fontSize: '13px',
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


