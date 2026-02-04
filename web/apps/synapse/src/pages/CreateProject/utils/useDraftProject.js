import { projectAtom } from "apps/synapse/src/providers/ProjectProvider";
import { useAtom } from "jotai";
import React from "react";

export const useDraftProject = () => {
  const [project, setProject] = useAtom(projectAtom);

  // No draft project creation - project will be created after project expenditure payment
  React.useEffect(() => {
    // Reset project state when component mounts
    setProject(null);
  }, []);

  return { project, setProject };
};

