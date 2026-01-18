import { Button, Checkbox } from "@synapse/ui";
import { inject, observer } from "mobx-react";
import React, { useState } from "react";
import { cn } from "../../utils/bem";
import { Dropdown } from "@synapse/ui";
import { Menu } from "./Menu/Menu";

const injector = inject(({ store }) => {
  return {
    columns: Array.from(store.currentView?.targetColumns ?? []),
  };
});

const FieldsMenu = observer(
  ({ columns, WrapperComponent, onClick, onReset, selected, resetTitle }) => {
    const MenuItem = (col, onClick) => {
      return (
        <Menu.Item
          key={col.key}
          name={col.key}
          onClick={onClick}
          disabled={col.disabled}
        >
          {WrapperComponent && col.wra !== false ? (
            <WrapperComponent column={col} disabled={col.disabled}>
              {col.title}
            </WrapperComponent>
          ) : (
            col.title
          )}
        </Menu.Item>
      );
    };

    return (
      <Menu
        size="small"
        selectedKeys={selected ? [selected] : ["none"]}
        closeDropdownOnItemClick={false}
      >
        {onReset &&
          MenuItem(
            {
              key: "none",
              title: resetTitle ?? "Default",
              wrap: false,
            },
            onReset
          )}

        {columns.map((col) => {
          if (col.children) {
            return (
              <Menu.Group key={col.key} title={col.title}>
                {col.children.map((col) => MenuItem(col, () => onClick?.(col)))}
              </Menu.Group>
            );
          }
          if (!col.parent) {
            return MenuItem(col, () => onClick?.(col));
          }

          return null;
        })}
      </Menu>
    );
  }
);

// Modern toolbar dropdown button style
// Modern toolbar dropdown button styles moved to TabPanel.scss (.dm-toolbar-button)

export const FieldsButton = injector(
  ({
    columns,
    size,
    style,
    wrapper,
    title,
    icon,
    className,
    trailingIcon,
    onClick,
    onReset,
    resetTitle,
    filter,
    selected,
    tooltip,
    tooltipTheme = "dark",
    openUpwardForShortViewport = true,
    "data-testid": dataTestId,
  }) => {
    const [isHovered, setIsHovered] = useState(false);
    const content = [];

    if (title)
      content.push(
        <React.Fragment key="f-button-title">{title}</React.Fragment>
      );

    const baseStyle = {
      // Spread custom style first (so it can be partially overridden if needed like minWidth)
      ...style,
      // Core styles
      background: 'black',
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
      gap: '6px',
      fontFamily: "'Space Grotesk', system-ui, -apple-system, sans-serif",
      outline: 'none',
      transition: 'all 0.15s ease',
      // Hover-dependent styles MUST be last so they can't be overridden
      border: `1px solid ${isHovered ? 'rgba(139, 92, 246, 0.5)' : 'rgba(55, 65, 81, 0.5)'}`,
      boxShadow: isHovered ? '0 0 12px rgba(139, 92, 246, 0.15)' : 'none',
    };

    const renderButton = () => {
      return (
        <button
          data-testid={dataTestId}
          className={className}
          style={baseStyle}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
        >
          {icon && <span style={{ display: 'flex', alignItems: 'center' }}>{icon}</span>}
          {content.length ? content : null}
          {trailingIcon && <span style={{ display: 'flex', alignItems: 'center' }}>{trailingIcon}</span>}
        </button>
      );
    };

    return (
      <Dropdown.Trigger
        content={
          <FieldsMenu
            columns={filter ? columns.filter(filter) : columns}
            WrapperComponent={wrapper}
            onClick={onClick}
            size={size}
            onReset={onReset}
            selected={selected}
            resetTitle={resetTitle}
          />
        }
        style={{ maxHeight: 280, overflow: "auto" }}
        openUpwardForShortViewport={openUpwardForShortViewport}
      >
        {tooltip ? (
          <div
            className={`${cn(
              "field-button"
            ).toClassName()} h-[40px] flex items-center`}
            style={{ zIndex: 1000 }}
          >
            <button
              data-testid={dataTestId}
              className={className}
              style={baseStyle}
              onMouseEnter={() => setIsHovered(true)}
              onMouseLeave={() => setIsHovered(false)}
              title={tooltip}
            >
              {icon && <span style={{ display: 'flex', alignItems: 'center' }}>{icon}</span>}
              {content.length ? content : null}
              {trailingIcon && <span style={{ display: 'flex', alignItems: 'center' }}>{trailingIcon}</span>}
            </button>
          </div>
        ) : (
          renderButton()
        )}
      </Dropdown.Trigger>
    );
  }
);

FieldsButton.Checkbox = observer(({ column, children, disabled }) => {
  return (
    <Checkbox
      size="small"
      checked={!column.hidden}
      onChange={column.toggleVisibility}
      style={{ width: "100%", height: "100%" }}
      disabled={disabled}
    >
      {children}
    </Checkbox>
  );
});
