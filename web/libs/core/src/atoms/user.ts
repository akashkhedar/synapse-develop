import type { APIUser } from "@synapse/core/types/user";
import { getApiInstance } from "../lib/api-provider/api-instance";
import { atomWithMutation, atomWithQuery, queryClientAtom } from "jotai-tanstack-query";

// Helper function to check if current path is public
const isPublicRoute = () => {
  const publicPaths = ['/', '/login', '/signup-client', '/annotators', '/services', '/about', '/contact', '/security', '/careers', '/blog'];
  return publicPaths.some(path => window.location.pathname === path || window.location.pathname.startsWith(path + '/'));
};

export const currentUserAtom = atomWithQuery(() => {
  return {
    queryKey: ["current-user"],
    enabled: !isPublicRoute(), // Only enable query on authenticated routes
    async queryFn() {
      // Double-check before making the API call
      if (isPublicRoute()) {
        throw new Error("Cannot fetch user on public route");
      }
      const api = getApiInstance();
      return await api.invoke<APIUser>("me");
    },
  };
});

export const currentUserUpdateAtom = atomWithMutation((get) => ({
  mutationKey: ["update-current-user"],
  async mutationFn({ pk, user }: { pk: number; user: Partial<APIUser> }) {
    const api = getApiInstance();
    return await api.invoke<APIUser>("updateUser", { pk }, { body: user });
  },

  onSettled() {
    const queryClient = get(queryClientAtom);
    queryClient.invalidateQueries({ queryKey: ["current-user"] });
  },
}));

