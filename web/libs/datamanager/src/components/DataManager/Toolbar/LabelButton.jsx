import { inject } from "mobx-react";
import { Button, ButtonGroup } from "@synapse/ui";
import { Interface } from "../../Common/Interface";
import { useCallback, useEffect, useRef, useState } from "react";
import { IconChevronDown } from "@synapse/icons";
import { Dropdown } from "@synapse/ui";
import { Menu } from "../../Common/Menu/Menu";
import { cn } from "../../../utils/bem";

const injector = inject(({ store }) => {
  const { dataStore, currentView } = store;
  const totalTasks = store.project?.task_count ?? store.project?.task_number ?? 0;
  const foundTasks = dataStore?.total ?? 0;
  const canAnnotate = store.SDK?.canAnnotate !== false;

  const isExpert = store?.SDK?.isExpert || false;

  return {
    store,
    canLabel: (totalTasks > 0 || foundTasks > 0) && canAnnotate, // Only allow labeling if user can annotate
    canAnnotate,
    isExpert,
    target: currentView?.target ?? "tasks",
    selectedCount: currentView?.selectedCount,
    allSelected: currentView?.allSelected,
  };
});

export const LabelButton = injector(({ store, canLabel, canAnnotate, isExpert, size, target, selectedCount }) => {
  const disabled = target === "annotations";
  const triggerRef = useRef();
  const [isOpen, setIsOpen] = useState(false);

  const handleClickOutside = useCallback((e) => {
    const el = triggerRef.current;

    if (el && !el.contains(e.target)) {
      setIsOpen(false);
    }
  }, []);

  useEffect(() => {
    document.addEventListener("click", handleClickOutside, { capture: true });

    return () => {
      document.removeEventListener("click", handleClickOutside, {
        capture: true,
      });
    };
  }, []);

  const onLabelAll = () => {
    localStorage.setItem("dm:labelstream:mode", "all");
    store.startLabelStream();
  };

  const onLabelVisible = () => {
    localStorage.setItem("dm:labelstream:mode", "filtered");
    store.startLabelStream();
  };

  const triggerStyle = {
    width: 24,
    padding: 0,
    borderTopLeftRadius: 0,
    borderBottomLeftRadius: 0,
    borderBottomRightRadius: isOpen ? 0 : undefined,
    boxShadow: "none",
  };

  const primaryStyle = {
    width: 160,
    padding: 0,
    borderTopRightRadius: 0,
    borderBottomRightRadius: 0,
    borderBottomLeftRadius: isOpen ? 0 : undefined,
  };

  const secondStyle = {
    width: triggerStyle.width + primaryStyle.width,
    padding: 0,
    display: isOpen ? "flex" : "none",
    position: "absolute",
    zIndex: 10,
    borderTopLeftRadius: 0,
    borderTopRightRadius: 0,
  };

  selectedCount;

  // Show view-only badge if user cannot annotate
  if (!canAnnotate) {
    return (
      <Interface name="viewOnlyBadge">
        <div style={{ 
          padding: '6px 12px', 
          backgroundColor: '#FEF3C7', 
          color: '#92400E',
          borderRadius: '6px',
          fontSize: '13px',
          fontWeight: 500,
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}>
          🔒 View Only Mode
        </div>
      </Interface>
    );
  }

  return canLabel ? (
    <Interface name="labelButton">
      <div>
        <ButtonGroup className="button-group">
          <Button
            size={size ?? "small"}
            // variant="primary"
            look="outlined"
            disabled={disabled}
            style={{
              width: '160px',
              background: 'black',
              border: '1px solid rgba(55, 65, 81, 0.5)',
              borderRight: 'none',
              borderRadius: '10px 0 0 10px',
              color: '#c4b5fd',
              fontWeight: 600,
              fontSize: '13px',
              height: '32px',
              padding: '0 14px',
              cursor: disabled ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              opacity: disabled ? 0.5 : 1,
            }}
            onClick={onLabelAll}
          >
            {isExpert ? "Review" : "Label"} {selectedCount ? selectedCount : "All"} Task
            {!selectedCount || selectedCount > 1 ? "s" : ""}
          </Button>
          <Dropdown.Trigger
            align="bottom-right"
            content={
              <Menu size="compact">
                <Menu.Item onClick={onLabelVisible}>{isExpert ? "Review" : "Label"} Tasks As Displayed</Menu.Item>
              </Menu>
            }
          >
            <Button 
                size={size} 
                look="outlined" 
                variant="primary" 
                aria-label={"Toggle open"}
                style={{
                  width: '24px',
                  padding: 0,
                  background: 'black',
                  border: '1px solid rgba(55, 65, 81, 0.5)',
                  borderLeft: 'none',
                  borderRadius: '0 10px 10px 0',
                  color: '#c4b5fd',
                  height: '32px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
            >
              <IconChevronDown />
            </Button>
          </Dropdown.Trigger>
        </ButtonGroup>
      </div>
    </Interface>
  ) : null;
});

