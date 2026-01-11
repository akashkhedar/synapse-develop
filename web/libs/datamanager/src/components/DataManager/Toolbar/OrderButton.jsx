import { IconSortDown, IconSortUp } from "@synapse/icons";
import { Button, ButtonGroup } from "@synapse/ui";
import { inject } from "mobx-react";
import { FieldsButton } from "../../Common/FieldsButton";
import { Space } from "../../Common/Space/Space";

const injector = inject(({ store }) => {
  const view = store?.currentView;

  return {
    view,
    ordering: view?.currentOrder,
  };
});

// Modern order button styles
const orderButtonStyle = {
  background: 'rgba(139, 92, 246, 0.08)',
  border: '1px solid rgba(139, 92, 246, 0.3)',
  color: '#a78bfa',
  borderRadius: '8px 0 0 8px',
  fontWeight: 500,
  fontSize: '13px',
};

const sortToggleStyle = {
  background: 'rgba(55, 65, 81, 0.4)',
  border: '1px solid rgba(75, 85, 99, 0.5)',
  borderLeft: 'none',
  color: '#9ca3af',
  borderRadius: '0 8px 8px 0',
  padding: '8px 10px',
  minWidth: '36px',
};

const sortToggleActiveStyle = {
  background: 'rgba(139, 92, 246, 0.15)',
  border: '1px solid rgba(139, 92, 246, 0.4)',
  borderLeft: 'none',
  color: '#a78bfa',
  borderRadius: '0 8px 8px 0',
  padding: '8px 10px',
  minWidth: '36px',
};

export const OrderButton = injector(({ size, ordering, view, ...rest }) => {
  return (
    <Space style={{ fontSize: 12 }}>
      <ButtonGroup collapsed {...rest}>
        <FieldsButton
          size={size}
          style={{ ...orderButtonStyle, minWidth: 80, textAlign: "left" }}
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
                  color: '#8b5cf6',
                }}
              >
                {column?.icon}
              </div>
            </Space>
          )}
          openUpwardForShortViewport={false}
        />

        
      </ButtonGroup>
    </Space>
  );
});


