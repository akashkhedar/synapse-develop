import { observer } from "mobx-react";
import { useSDK } from "../../providers/SDKProvider";
import { cn } from "../../utils/bem";
import { LabelingViewOnly } from "./LabelingViewOnly";
import "./Label.scss";

/**
 * View-only labeling component for organization members
 * Displays tasks and annotations without any editing capabilities
 */
export const ViewOnlyLabel = observer(() => {
  const sdk = useSDK();
  const store = sdk.store;

  return (
    <div className={cn("label").toClassName()}>
      <LabelingViewOnly store={store} />
    </div>
  );
});

