import { getJestProjectsAsync } from "@nx/jest";
import { pathsToModuleNameMapper } from "ts-jest";

export default async () => ({
  projects: await getJestProjectsAsync(),
  moduleNameMapper: pathsToModuleNameMapper(
    {
      "@synapse/core": ["libs/core/src/index.ts"],
      "@synapse/datamanager": ["libs/datamanager/src/index.js"],
      "@synapse/editor": ["libs/editor/src/index.js"],
      "@synapse/frontend-test/*": ["libs/frontend-test/src/*"],
      "@synapse/ui": ["libs/ui/src/index.ts"],
      "@synapse/icons": ["libs/ui/src/assets/icons"],
      "@synapse/shad/*": ["./libs/ui/src/shad/*"],
    },
    { prefix: "<rootDir>/../../" },
  ),
});

