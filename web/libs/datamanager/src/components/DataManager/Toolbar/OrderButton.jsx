import { IconSortDown, IconSortUp } from "@synapse/icons";
import { Button, ButtonGroup } from "@synapse/ui";
import { inject } from "mobx-react";
import { FieldsButton } from "../../Common/FieldsButton";
import { cn } from "../../../utils/bem";
import "./TabPanel.scss";
import { Space } from "../../Common/Space/Space";

const injector = inject(({ store }) => {
  const view = store?.currentView;

  return {
    view,
    ordering: view?.currentOrder,
  };
});

// Modern order button styles moved to TabPanel.scss (.dm-toolbar-button)

// Modern toolbar button style (Inline to match DensityToggle pattern)


export const OrderButton = injector(({ size, ordering, view, ...rest }) => {
  return (
    <Space style={{ fontSize: 12 }}>
        <FieldsButton
          size={size}
          style={{
            background: 'black',
            border: '1px solid rgba(55, 65, 81, 0.5)',
            borderRadius: '10px',
            color: '#c4b5fd',
            fontWeight: 600,
            fontSize: '13px',
            height: '32px',
            padding: '0 14px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            minWidth: '80px',
          }}
          title={ordering ? ordering.column?.title : "Order by"}
          onClick={(col) => view.setOrdering(col.id)}
          onReset={() => view.setOrdering(null)}
          resetTitle="Default"
          selected={ordering?.field}
          filter={(col) => {
            return col.orderable ?? col.original?.orderable;
          }}
          wrapper={({ column, children }) => (
            <Space style={{ width: "100%", justifyContent: "space-between" }}>
              {children}

              <div
                style={{
                  width: 24,
                  height: 24,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "#c4b5fd", 
                }}
              >
                {column?.icon}
              </div>
            </Space>
          )}
          openUpwardForShortViewport={false}
        />
    </Space>
  );
});
