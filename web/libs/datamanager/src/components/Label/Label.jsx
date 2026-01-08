import { inject } from "mobx-react";
import { observer } from "mobx-react-lite";
import { useCallback, useEffect, useMemo, useRef } from "react";
import {
  IconChevronDown,
  IconChevronLeft,
  IconGearNewUI,
} from "@synapse/icons";
import { cn } from "../../utils/bem";
import { Button } from "@synapse/ui";
import { FieldsButton } from "../Common/FieldsButton";
import { Icon } from "../Common/Icon/Icon";
import { Resizer } from "../Common/Resizer/Resizer";
import { Space } from "../Common/Space/Space";
import { DataView } from "../MainView";
import "./Label.scss";

// Todo: consider renaming this file to something like LabelingWrapper as it is not a Label component
const LabelingHeader = ({ SDK, onClick, isExplorerMode }) => {
  return (
    <div
      className={cn("label-view")
        .elem("header")
        .mod({ labelStream: !isExplorerMode })
        .toClassName()}
    >
      <Space size="large">
        {SDK.interfaceEnabled("backButton") && (
          <Button
            icon={<IconChevronLeft style={{ marginRight: 4, fontSize: 16 }} />}
            type="link"
            onClick={onClick}
            style={{ fontSize: 18, padding: 0, color: "black" }}
          >
            Back
          </Button>
        )}

        {isExplorerMode ? (
          <FieldsButton
            wrapper={FieldsButton.Checkbox}
            icon={<Icon icon={IconGearNewUI} />}
            trailingIcon={<Icon icon={IconChevronDown} />}
            title={"Fields"}
          />
        ) : null}
      </Space>
    </div>
  );
};

const injector = inject(({ store }) => {
  return {
    store,
    loading: store?.loadingData,
  };
});

/**
 * @param {{store: import("../../stores/AppStore").AppStore}} param1
 */
export const Labeling = injector(
  observer(({ store, loading }) => {
    const sfRef = useRef();
    const SDK = store?.SDK;
    const view = store?.currentView;
    const { isExplorerMode } = store;

    const isLabelStream = useMemo(() => {
      return SDK.mode === "labelstream";
    }, []);

    const closeLabeling = useCallback(() => {
      store.closeLabeling();
    }, [store]);

    const initLabeling = useCallback(() => {
      if (!SDK.sf) SDK.initSF(sfRef.current);
      SDK.startLabeling();
    }, []);

    useEffect(() => {
      if (!isLabelStream) SDK.on("taskSelected", initLabeling);

      return () => {
        if (!isLabelStream) SDK.off("taskSelected", initLabeling);
      };
    }, []);

    useEffect(() => {
      if ((!SDK.sf && store.dataStore.selected) || isLabelStream) {
        initLabeling();
      }
    }, []);

    useEffect(() => {
      return () => SDK.destroySF();
    }, []);

    const onResize = useCallback((width) => {
      view.setLabelingTableWidth(width);
      // trigger resize events inside SF
      window.dispatchEvent(new Event("resize"));
    }, []);

    return (
      <div className={cn("label-view").mod({ loading }).toClassName()}>
        {SDK.interfaceEnabled("labelingHeader") && (
          <LabelingHeader
            SDK={SDK}
            onClick={closeLabeling}
            isExplorerMode={isExplorerMode}
          />
        )}

        <div className={cn("label-view").elem("content").toClassName()}>
          {isExplorerMode && (
            <div className={cn("label-view").elem("table").toClassName()}>
              <Resizer
                className={cn("label-view").elem("dataview").toClassName()}
                minWidth={202}
                showResizerLine={false}
                type={"quickview"}
                maxWidth={window.innerWidth * 0.35}
                initialWidth={view.labelingTableWidth} // hardcoded as in main-menu-trigger
                onResizeFinished={onResize}
                style={{ display: "flex", flex: 1, width: "100%" }}
              >
                <DataView />
              </Resizer>
            </div>
          )}

          <div
            className={cn("label-view")
              .elem("sf-wrapper")
              .mod({ mode: isExplorerMode ? "explorer" : "labeling" })
              .toClassName()}
          >
            {loading && (
              <div
                className={cn("label-view")
                  .elem("waiting")
                  .mod({ animated: true })
                  .toClassName()}
              />
            )}
            <div
              ref={sfRef}
              id="synapse-dm"
              className={cn("label-view").elem("sf-container").toClassName()}
              key="synapse"
            />
          </div>
        </div>
      </div>
    );
  })
);
