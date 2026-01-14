import { inject, observer } from "mobx-react";
import React, { useEffect, useRef } from "react";
import { IconChevronDown } from "@synapse/icons";
import { Filters } from "../Filters/Filters";
import { Badge } from "./Badge/Badge";
import { Button } from "@synapse/ui";
import { Dropdown } from "@synapse/ui";
import { Icon } from "./Icon/Icon";

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

        return (
          <Button
            ref={ref}
            size="small"
            look="outlined"
            onClick={() => sidebarEnabled && viewsStore.toggleSidebar()}
            trailing={<Icon icon={IconChevronDown} />}
            aria-label="Filters"
            style={{
              "--background-color": "rgba(139, 92, 246, 0.08)",
              "--border-color": "rgba(139, 92, 246, 0.3)",
              "--border-outline": "rgba(139, 92, 246, 0.3)",
              "--text-color": "#a78bfa",
              "--text-outline": "#a78bfa",
              "--background-color-hover": "rgba(139, 92, 246, 0.15)",
              borderRadius: "8px",
              fontWeight: 500,
              fontSize: "13px",
            }}
            {...rest}
          >
            Filters{" "}
            {hasFilters && (
              <Badge
                size="small"
                style={{
                  marginLeft: 6,
                  background: "linear-gradient(135deg, #8b5cf6, #7c3aed)",
                  color: "white",
                  fontWeight: 700,
                  fontSize: "10px",
                  fontFamily:
                    "'Space Grotesk', system-ui, -apple-system, sans-serif",
                  padding: "2px 6px",
                  borderRadius: "10px",
                  boxShadow: "0 2px 6px rgba(139, 92, 246, 0.3)",
                }}
              >
                {activeFiltersNumber}
              </Badge>
            )}
          </Button>
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
