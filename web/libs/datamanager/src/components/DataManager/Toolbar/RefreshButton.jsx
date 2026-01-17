import { inject } from "mobx-react";
import { IconRefresh } from "@synapse/icons";
import { useMemo } from "react";
import "./TabPanel.scss";
import { Button } from "@synapse/ui";

const injector = inject(({ store }) => {
  return {
    store,
    needsDataFetch: store.needsDataFetch,
    projectFetch: store.projectFetch,
  };
});

// Modern refresh button styles
const refreshButtonStyle = {
  background: 'black',
  border: '1px solid rgba(55, 65, 81, 0.5)',
  color: '#c4b5fd',
  borderRadius: '10px',
  fontFamily: "'Space Grotesk', system-ui, -apple-system, sans-serif",
  fontWeight: 600,
  minWidth: '36px',
  padding: '0 10px',
};

const refreshButtonActiveStyle = {
  background: 'rgba(139, 92, 246, 0.2)',
  border: '1px solid rgba(55, 65, 81, 0.5)',
  color: '#c4b5fd',
  borderRadius: '10px',
  fontFamily: "'Space Grotesk', system-ui, -apple-system, sans-serif",
  fontWeight: 600,
  minWidth: '36px',
  padding: '0 10px',
};

export const RefreshButton = injector(({ store, needsDataFetch, projectFetch, size, style, ...rest }) => {
  return (
    <Button
      size={size ?? "small"}
      style={needsDataFetch ? refreshButtonActiveStyle : refreshButtonStyle}
      waiting={projectFetch}
      aria-label="Refresh data"
      onClick={async () => {
        await store.fetchProject({ force: true, interaction: "refresh" });
        await store.currentView?.reload();
      }}
    >
      <IconRefresh />
    </Button>
  );
});

