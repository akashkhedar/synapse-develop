import { types } from "mobx-state-tree";
import { User } from "./Users";
import { StringOrNumberID } from "./types";
import { FF_DISABLE_GLOBAL_USER_FETCHING, isFF } from "../utils/feature-flags";

// Create a union type that can handle both user references and direct user objects
const UserOrReference = types.union({
  dispatcher: (snapshot) => {
    // If it's a full user object (has firstName, email, etc.), use User model
    if (
      snapshot &&
      typeof snapshot === "object" &&
      (snapshot.firstName || snapshot.email || snapshot.username)
    ) {
      return User;
    }
    // Otherwise, it's a reference to a user ID
    return types.reference(User);
  },
  cases: {
    [User.name]: User,
    reference: types.reference(User),
  },
});

export const Assignee = types
  .model("Assignee", {
    id: StringOrNumberID,
    user: types.late(() => UserOrReference),
    review: types.maybeNull(
      types.enumeration(["accepted", "rejected", "fixed"])
    ),
    reviewed: types.maybeNull(types.boolean),
    annotated: types.maybeNull(types.boolean),
  })
  .views((self) => ({
    get firstName() {
      return self.user.firstName;
    },
    get lastName() {
      return self.user.lastName;
    },
    get username() {
      return self.user.username;
    },
    get email() {
      return self.user.email;
    },
    get lastActivity() {
      return self.user.lastActivity;
    },
    get avatar() {
      return self.user.avatar;
    },
    get initials() {
      return self.user.initials;
    },
    get fullName() {
      return self.user.fullName;
    },
  }))
  .preProcessSnapshot((sn) => {
    // Handle null, undefined, or invalid input - return a minimal valid object
    if (!sn || (typeof sn !== "number" && typeof sn !== "object")) {
      // Return a placeholder that won't break the model
      return {
        id: 0,
        user: {
          id: 0,
          firstName: "",
          lastName: "",
          username: "",
          email: "",
          lastActivity: "",
          initials: "??",
        },
        annotated: null,
        review: null,
        reviewed: null,
      };
    }

    let result = sn;

    if (typeof sn === "number") {
      result = {
        id: sn,
        user: sn,
        annotated: true,
        review: null,
        reviewed: false,
      };
    } else {
      // Handle both old format (id, user) and new format (user_id, ...)
      // Old format: {id: 1, user: 1, annotated: true, ...}
      // New format: {user_id: 1, firstName: "...", lastName: "...", ...}

      // If data already has id and user fields (old format), use as-is
      if (sn.id !== undefined && sn.user !== undefined) {
        result = sn;
      } else {
        // New format with user_id and user properties
        const { user_id, annotated, review, reviewed, ...userProps } = sn;

        // Skip if no user_id - return placeholder
        if (user_id === undefined || user_id === null) {
          return {
            id: 0,
            user: {
              id: 0,
              firstName: "",
              lastName: "",
              username: "",
              email: "",
              lastActivity: "",
              initials: "??",
            },
            annotated: null,
            review: null,
            reviewed: null,
          };
        }

        // Check if we have user properties (firstName, email, username, etc.)
        const hasUserProperties = Object.keys(userProps).length > 0;

        // If we have user properties, always create a user object to avoid reference errors
        // This prevents "Failed to resolve reference" errors when users aren't in the global store
        if (hasUserProperties) {
          // Build a complete user object with all required fields
          const user = {
            id: user_id,
            firstName: userProps.firstName || "",
            lastName: userProps.lastName || "",
            username:
              userProps.username || userProps.email?.split("@")[0] || "",
            email: userProps.email || "",
            lastActivity: userProps.lastActivity || "",
            avatar: userProps.avatar || null,
            initials:
              userProps.initials ||
              (
                (userProps.firstName || userProps.email || "").charAt(0) +
                (userProps.lastName || "").charAt(0)
              ).toLowerCase() ||
              "??",
          };
          result = {
            id: user_id,
            user: user,
            annotated: annotated ?? null,
            review: review ?? null,
            reviewed: reviewed ?? null,
          };
        } else {
          // No user properties - use reference (may cause issues if user not in store)
          result = {
            id: user_id,
            user: user_id,
            annotated: annotated ?? null,
            review: review ?? null,
            reviewed: reviewed ?? null,
          };
        }
      }
    }

    return result;
  });

