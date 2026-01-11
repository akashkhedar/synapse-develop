import { inject } from "mobx-react";
import { IconRefresh } from "@synapse/icons";
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
  background: 'rgba(139, 92, 246, 0.08)',
  border: '1px solid rgba(139, 92, 246, 0.3)',
  color: '#a78bfa',
  borderRadius: '8px',
  fontFamily: "'Space Grotesk', system-ui, -apple-system, sans-serif",
  fontWeight: 500,
  transition: 'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)',
  minWidth: '36px',
  padding: '0 10px',
};

const refreshButtonActiveStyle = {
  background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(168, 85, 247, 0.15))',
  border: '1px solid rgba(139, 92, 246, 0.5)',
  color: '#c4b5fd',
  borderRadius: '8px',
  fontFamily: "'Space Grotesk', system-ui, -apple-system, sans-serif",
  fontWeight: 600,
  transition: 'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)',
  minWidth: '36px',
  padding: '0 10px',
  boxShadow: '0 0 12px rgba(139, 92, 246, 0.3)',
};

export const RefreshButton = injector(({ store, needsDataFetch, projectFetch, size, style, ...rest }) => {
  return (
    <Button
      size={size ?? "small"}
      look={needsDataFetch ? "filled" : "outlined"}
      variant={needsDataFetch ? "primary" : "neutral"}
      waiting={projectFetch}
      aria-label="Refresh data"
      style={needsDataFetch ? refreshButtonActiveStyle : refreshButtonStyle}
      onClick={async () => {
        await store.fetchProject({ force: true, interaction: "refresh" });
        await store.currentView?.reload();
      }}
    >
      <IconRefresh />
    </Button>
  );
});

