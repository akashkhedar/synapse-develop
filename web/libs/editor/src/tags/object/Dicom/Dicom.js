import { getRoot, types } from "mobx-state-tree";
import ObjectBase from "../Base";
import { AnnotationMixin } from "../../../mixins/AnnotationMixin";
import { IsReadyWithDepsMixin } from "../../../mixins/IsReadyMixin";
import { customTypes } from "../../../core/CustomTypes";
import { parseValue } from "../../../utils/data";

const TagAttrs = types.model({
  value: types.maybeNull(types.string),
  name: types.maybeNull(types.string),
  zoom: types.optional(types.boolean, true),
  pan: types.optional(types.boolean, true),
  // Default Window/Level presets
  windowcenter: types.optional(types.number, 40),
  windowwidth: types.optional(types.number, 400),
});

const Model = types
  .model({
    type: "dicom",
  })
  .views((self) => ({
    get hasStates() {
    // TODO: Implement region/annotation support
        return true;
    },

    // Simulate Image model region support
    get regs() {
        return self.annotation?.regionStore.regions.filter((r) => r.object === self) || [];
    },

    findRegion(params) {
        return self.regs.find((r) => r.id === params.id);
    },

    get isReady() {
        return true;
    },

    get store() {
      return getRoot(self);
    },

    get parsedValue() {
      return parseValue(self.value, self.store.task.dataObj);
    },

    // Mock stageRef for tools that expect it (like Brush)
    get stageRef() {
        return {
            content: { scrollLeft: 0, scrollTop: 0 },
            container: () => ({ style: {} }),
            getPointerPosition: () => ({ x: 0, y: 0 }),
            batchDraw: () => {},
        };
    },

    states() {
      return self.annotation.toNames.get(self.name);
    },

    activeStates() {
      const states = self.states();
      return states && states.filter((s) => s.isSelected && s.type.includes("labels"));
    },
  }));

const DicomModel = types.compose(
  "DicomModel",
  ObjectBase,
  TagAttrs,
  AnnotationMixin,
  IsReadyWithDepsMixin,
  Model
);

console.log("DicomModel file evaluated");
export default DicomModel;
