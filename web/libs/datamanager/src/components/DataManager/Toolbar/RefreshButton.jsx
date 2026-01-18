import { inject } from "mobx-react";
import { IconRefresh } from "@synapse/icons";
import { useState } from "react";
import "./TabPanel.scss";

const injector = inject(({ store }) => {
  return {
    store,
    needsDataFetch: store.needsDataFetch,
    projectFetch: store.projectFetch,
  };
});

export const RefreshButton = injector(({ store, needsDataFetch, projectFetch, size, style, ...rest }) => {
  const [isHovered, setIsHovered] = useState(false);
  
  return (
    <button
      aria-label="Refresh data"
      disabled={projectFetch}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={async () => {
        await store.fetchProject({ force: true, interaction: "refresh" });
        await store.currentView?.reload();
      }}
      style={{
        background: needsDataFetch ? 'rgba(139, 92, 246, 0.2)' : 'black',
        border: `1px solid ${isHovered && !projectFetch ? 'rgba(139, 92, 246, 0.5)' : 'rgba(55, 65, 81, 0.5)'}`,
        borderRadius: '10px',
        color: '#c4b5fd',
        fontWeight: 600,
        fontSize: '13px',
        height: '32px',
        minWidth: '36px',
        padding: '0 10px',
        cursor: projectFetch ? 'wait' : 'pointer',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: "'Space Grotesk', system-ui, -apple-system, sans-serif",
        outline: 'none',
        transition: 'all 0.15s ease',
        boxShadow: isHovered && !projectFetch ? '0 0 12px rgba(139, 92, 246, 0.15)' : 'none',
        opacity: projectFetch ? 0.7 : 1,
      }}
    >
      <IconRefresh style={{ 
        width: 16, 
        height: 16,
        animation: projectFetch ? 'spin 1s linear infinite' : 'none',
      }} />
    </button>
  );
});

