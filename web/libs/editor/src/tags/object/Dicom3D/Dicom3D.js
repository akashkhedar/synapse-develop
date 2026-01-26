import { getRoot, types } from "mobx-state-tree";
import ObjectBase from "../Base";
import { AnnotationMixin } from "../../../mixins/AnnotationMixin";
import { IsReadyWithDepsMixin } from "../../../mixins/IsReadyMixin";
import { parseValue } from "../../../utils/data";

const TagAttrs = types.model({
  value: types.maybeNull(types.string),
  name: types.maybeNull(types.string),
  mode: types.optional(types.enumeration(["stack", "volume", "3d"]), "volume"), // Default to volume
});

const Model = types
  .model({
    type: "dicom3d",
  })
  .views((self) => ({
    get hasStates() {
      return true;
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
  }));

const Dicom3DModel = types.compose(
  "Dicom3DModel",
  ObjectBase,
  TagAttrs,
  AnnotationMixin,
  IsReadyWithDepsMixin,
  Model
);

export { Dicom3DModel };
