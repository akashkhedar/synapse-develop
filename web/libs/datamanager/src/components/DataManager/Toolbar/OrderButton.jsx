import { IconChevronDown, IconSortDown, IconSortUp } from "@synapse/icons";
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

export const OrderButton = injector(({ size, ordering, view, ...rest }) => {
  return (
    <Space style={{ fontSize: 12 }}>
        <FieldsButton
          size={size}
          style={{ minWidth: '80px' }}
          title={ordering ? ordering.column?.title : "Order by"}
          trailingIcon={<IconChevronDown style={{ width: 16, height: 16 }} />}
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
