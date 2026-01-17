import { inject } from "mobx-react";
import React from "react";
import { cn } from "../../utils/bem";
import { Button } from "@synapse/ui";
import { FilterLine } from "./FilterLine/FilterLine";
import { IconChevronRight, IconPlus } from "@synapse/icons";
import "../DataManager/Toolbar/TabPanel.scss"; // Import shared toolbar styles
import "./Filters.scss";

const injector = inject(({ store }) => ({
  store,
  views: store.viewsStore,
  currentView: store.currentView,
  filters: store.currentView?.currentFilters ?? [],
}));

export const Filters = injector(({ views, currentView, filters }) => {
  const { sidebarEnabled } = views;

  const fields = React.useMemo(
    () =>
      currentView.availableFilters.reduce((res, filter) => {
        const target = filter.field.target;
        const groupTitle = target
          .split("_")
          .map((s) =>
            s
              .split("")
              .map((c, i) => (i === 0 ? c.toUpperCase() : c))
              .join("")
          )
          .join(" ");

        const group = res[target] ?? {
          id: target,
          title: groupTitle,
          options: [],
        };

        group.options.push({
          value: filter.id,
          title: filter.field.title,
          original: filter,
        });

        return { ...res, [target]: group };
      }, {}),
    [currentView.availableFilters]
  );

// Modern toolbar button style (Inline to match DensityToggle pattern)
const toolbarButtonStyle = {
  background: "rgba(139, 92, 246, 0.2)",
  border: "1px solid rgba(139, 92, 246, 0.3)",
  borderRadius: "8px",
  color: "#c4b5fd",
  fontSize: "13px",
  fontWeight: 500,
  fontFamily: "'Space Grotesk', system-ui, sans-serif",
  height: "32px",
  padding: "0 16px",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
};

  return (
    <div
      className={cn("filters").mod({ sidebar: sidebarEnabled }).toClassName()}
    >
      <div
        className={cn("filters")
          .elem("list")
          .mod({ withFilters: !!filters.length })
          .toClassName()}
      >
        {filters.length ? (
          filters.map((filter, i) => (
            <FilterLine
              index={i}
              filter={filter}
              view={currentView}
              sidebar={sidebarEnabled}
              value={filter.currentValue}
              key={`${filter.filter.id}-${i}`}
              availableFilters={Object.values(fields)}
              dropdownClassName={cn("filters").elem("selector").toClassName()}
            />
          ))
        ) : (
          <div className={cn("filters").elem("empty").toClassName()}>
            No filters applied
          </div>
        )}
      </div>
      <div className={cn("filters").elem("actions").toClassName()}>
        <Button
          size="small"
          look="outlined"
          onClick={() => currentView.createFilter()}
          leading={<IconPlus className="!h-3 !w-3" />}
          className="dm-toolbar-button"
          style={toolbarButtonStyle}
        >
          Add {filters.length ? "Another Filter" : "Filter"}
        </Button>

        {!sidebarEnabled ? (
          <Button
            look="outlined"
            type="link"
            size="small"
            tooltip="Pin to sidebar"
            onClick={() => views.expandFilters()}
            aria-label="Pin filters to sidebar"
            className="dm-toolbar-button"
            style={toolbarButtonStyle}
          >
            <IconChevronRight className="!w-4 !h-4" />
          </Button>
        ) : null}
      </div>
    </div>
  );
});
