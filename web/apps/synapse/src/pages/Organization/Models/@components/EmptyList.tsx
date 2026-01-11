import { Button } from "@synapse/ui";
import { IconSparks } from "@synapse/icons";
import { cn } from "apps/synapse/src/utils/bem";
import type { FC } from "react";
import "./EmptyList.scss";

export const EmptyList: FC = () => {
  return (
    <div className={cn("empty-models-list").toClassName()}>
      <div className={cn("empty-models-list").elem("content").toClassName()}>
        <div className={cn("empty-models-list").elem("icon").toClassName()}>
          <IconSparks />
        </div>
        <div className={cn("empty-models-list").elem("step").toClassName()}>01/</div>
        <div className={cn("empty-models-list").elem("title").toClassName()}>Create your first model</div>
        <div className={cn("empty-models-list").elem("caption").toClassName()}>
          Build a high-quality model to auto-label your data using LLMs
        </div>
        <Button aria-label="Create new model">Create Model</Button>
      </div>
    </div>
  );
};

