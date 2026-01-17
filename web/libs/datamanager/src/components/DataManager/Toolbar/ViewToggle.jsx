import { inject, observer } from "mobx-react";
import { RadioGroup } from "../../Common/RadioGroup/RadioGroup";
import { IconGrid, IconList } from "@synapse/icons";
import { Tooltip } from "@synapse/ui";

const viewInjector = inject(({ store }) => ({
  view: store.currentView,
}));

// Button style constants
const containerStyle = {
  background: 'black',
  border: '1px solid rgba(55, 65, 81, 0.5)',
  borderRadius: '10px',
  height: '32px',
  display: 'flex',
  alignItems: 'center',
  gap: '2px',
  padding: '3px',
};

const buttonStyle = {
  background: 'transparent',
  border: 'none',
  borderRadius: '7px',
  color: '#c4b5fd',
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  height: '26px',
  width: '26px',
  padding: '0',
};

const buttonActiveStyle = {
  ...buttonStyle,
  background: 'rgba(139, 92, 246, 0.2)',
};

export const ViewToggle = viewInjector(
  observer(({ view, size, ...rest }) => {
    return (
      <RadioGroup
        size={size}
        value={view.type}
        onChange={(e) => view.setType(e.target.value)}
        {...rest}
        style={containerStyle}
      >
        <Tooltip title="List view">
          <div>
            <RadioGroup.Button 
              value="list" 
              aria-label="Switch to list view"
              style={view.type === 'list' ? buttonActiveStyle : buttonStyle}
            >
              <IconList style={{ width: 16, height: 16 }} />
            </RadioGroup.Button>
          </div>
        </Tooltip>
        <Tooltip title="Grid view">
          <div>
            <RadioGroup.Button 
              value="grid" 
              aria-label="Switch to grid view"
              style={view.type === 'grid' ? buttonActiveStyle : buttonStyle}
            >
              <IconGrid style={{ width: 16, height: 16 }} />
            </RadioGroup.Button>
          </div>
        </Tooltip>
      </RadioGroup>
    );
  }),
);

export const DataStoreToggle = viewInjector(({ view, size, ...rest }) => {
  return (
    <RadioGroup value={view.target} size={size} onChange={(e) => view.setTarget(e.target.value)} {...rest}>
      <RadioGroup.Button value="tasks">Tasks</RadioGroup.Button>
      <RadioGroup.Button value="annotations" disabled>
        Annotations
      </RadioGroup.Button>
    </RadioGroup>
  );
});
