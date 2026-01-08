import { observer } from "mobx-react";
import { types } from "mobx-state-tree";

import BaseTool from "./Base";
import ToolMixin from "../mixins/Tool";

import { Tool } from "../components/Toolbar/Tool";

// Simple crosshair SVG icon
const CrosshairIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 2V8M12 16V22M2 12H8M16 12H22" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
    <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="2" fill="none"/>
  </svg>
);

const ToolView = observer(({ item }) => {
  return (
    <Tool
      active={item.crosshairEnabled}
      ariaLabel="crosshair"
      label="Crosshair"
      icon={<CrosshairIcon />}
      onClick={() => {
        item.toggleCrosshair();
      }}
    />
  );
});

const _Tool = types
  .model({
    crosshairEnabled: types.optional(types.boolean, false),
  })
  .views((self) => ({
    get viewClass() {
      return () => <ToolView item={self} />;
    },
  }))
  .actions((self) => ({
    toggleCrosshair() {
      self.crosshairEnabled = !self.crosshairEnabled;
      self.obj.setCrosshair(self.crosshairEnabled);
    },
  }));

const Crosshair = types.compose(_Tool.name, ToolMixin, BaseTool, _Tool);

export { Crosshair };

