import { inject, observer } from "mobx-react";
import React, { useEffect, useRef, useState } from "react";
import { IconChevronDown } from "@synapse/icons";
import { Filters } from "../Filters/Filters";
import { Badge } from "./Badge/Badge";
import { Button } from "@synapse/ui";
import { Dropdown } from "@synapse/ui";
import { Icon } from "./Icon/Icon";
import { cn } from "../../utils/bem";
import "../DataManager/Toolbar/TabPanel.scss"; // Import for toolbar-button styles

const buttonInjector = inject(({ store }) => {
  const { viewsStore, currentView } = store;

  return {
    viewsStore,
    sidebarEnabled: viewsStore?.sidebarEnabled ?? false,
    activeFiltersNumber: currentView?.filtersApplied ?? false,
  };
});

export const FiltersButton = buttonInjector(
  observer(
    React.forwardRef(
      (
        { activeFiltersNumber, size, sidebarEnabled, viewsStore, ...rest },
        ref
      ) => {
        const hasFilters = activeFiltersNumber > 0;
        const [isHovered, setIsHovered] = useState(false);

        return (
          <button
            {...rest}
            ref={ref}
            type="button"
            aria-label="Filters"
            onClick={() => {
              // When sidebar mode is enabled, clicking toggles the sidebar
              if (sidebarEnabled) {
                viewsStore?.toggleSidebar?.();
              }
              // Otherwise, Dropdown.Trigger handles the click to open dropdown
            }}
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
            }}
          >
            Filters
            {hasFilters && (
              <span
                style={{
                  background: "linear-gradient(135deg, #8b5cf6, #7c3aed)",
                  color: "white",
                  fontWeight: 700,
                  fontSize: "10px",
                  fontFamily: "'Space Grotesk', system-ui, -apple-system, sans-serif",
                  padding: "2px 6px",
                  borderRadius: "10px",
                  boxShadow: "0 2px 6px rgba(139, 92, 246, 0.3)",
                }}
              >
                {activeFiltersNumber}
              </span>
            )}
            <IconChevronDown style={{ width: 16, height: 16 }} />
          </button>
        );
      }
    )
  )
);

const injector = inject(({ store }) => {
  return {
    sidebarEnabled: store?.viewsStore?.sidebarEnabled ?? false,
  };
});

export const FiltersPane = injector(
  observer(({ sidebarEnabled, size, ...rest }) => {
    const dropdown = useRef();

    useEffect(() => {
      if (sidebarEnabled === true) {
        dropdown?.current?.close();
      }
    }, [sidebarEnabled]);

    return (
      <Dropdown.Trigger
        ref={dropdown}
        disabled={sidebarEnabled}
        content={<Filters />}
        openUpwardForShortViewport={false}
        isChildValid={(ele) => {
          return !!ele.closest("[data-radix-popper-content-wrapper]");
        }}
      >
        <FiltersButton {...rest} size={size} />
      </Dropdown.Trigger>
    );
  })
);
