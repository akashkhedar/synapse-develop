import { types } from "mobx-state-tree";
import { camelizeKeys } from "../utils/helpers";
import { StringOrNumberID } from "./types";

export const User = types
  .model("User", {
    id: StringOrNumberID,
    firstName: types.optional(types.string, ""),
    lastName: types.optional(types.string, ""),
    username: types.optional(types.string, ""),
    email: types.optional(types.string, ""),
    lastActivity: types.optional(types.string, ""),
    avatar: types.maybeNull(types.string),
    initials: types.optional(types.string, ""),
  })
  .views((self) => ({
    get fullName() {
      return [self.firstName, self.lastName]
        .filter((n) => !!n)
        .join(" ")
        .trim();
    },

    get displayName() {
      return self.fullName || (self.username ? self.username : self.email);
    },
  }))
  .preProcessSnapshot((sn) => {
    const processed = camelizeKeys(sn);
    // Ensure initials are generated if missing
    if (!processed.initials && (processed.firstName || processed.email)) {
      const first = (processed.firstName || processed.email || "").charAt(0);
      const last = (processed.lastName || "").charAt(0);
      processed.initials = (first + last).toLowerCase() || "??";
    }
    return processed;
  });

