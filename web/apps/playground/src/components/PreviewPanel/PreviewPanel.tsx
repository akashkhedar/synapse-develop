import { memo, useEffect, useRef } from "react";
import type { FC } from "react";
import { generateSampleTaskFromConfig } from "../../utils/generateSampleTask";
import { useAtom, useAtomValue, useSetAtom } from "jotai";
import {
  configAtom,
  errorAtom,
  loadingAtom,
  showPreviewAtom,
  interfacesAtom,
  annotationAtom,
  sampleTaskAtom,
  displayModeAtom,
} from "../../atoms/configAtoms";
import { onSnapshot } from "mobx-state-tree";

type PreviewPanelProps = {
  onAnnotationUpdate?: (annotation: any) => void;
};

// Clear localStorage of any Synapse:settings as it may cause issues with fullscreen mode
// if coming from the old playground
localStorage.removeItem("Synapse:settings");

export const PreviewPanel: FC<PreviewPanelProps> = memo(
  ({ onAnnotationUpdate }) => {
    const config = useAtomValue(configAtom);
    const loading = useAtomValue(loadingAtom);
    const error = useAtomValue(errorAtom);
    const interfaces = useAtomValue(interfacesAtom);
    const setAnnotation = useSetAtom(annotationAtom);
    const setSampleTask = useSetAtom(sampleTaskAtom);
    const displayMode = useAtomValue(displayModeAtom);
    const [showPreview, setShowPreview] = useAtom(showPreviewAtom);
    const rootRef = useRef<HTMLDivElement>(null);
    const sfInstance = useRef<any>(null);
    const rafId = useRef<number | null>(null);

    useEffect(() => {
      let Synapse: any;
      let dependencies: any;
      let snapshotDisposer: any;

      function cleanup() {
        if (typeof window !== "undefined" && (window as any).Synapse) {
          delete (window as any).Synapse;
        }
        setShowPreview(false);
        if (sfInstance.current) {
          try {
            sfInstance.current.destroy();
          } catch {
            // do nothing, it would otherwise complain about not being a node of the tree in HMR development scenarios
          }
          sfInstance.current = null;
        }
        if (rafId.current !== null) {
          cancelAnimationFrame(rafId.current);
          rafId.current = null;
        }
        if (snapshotDisposer) {
          snapshotDisposer();
          snapshotDisposer = null;
        }
      }

      async function loadSF() {
        dependencies = await import("@synapse/editor");
        Synapse = dependencies.Synapse;
        if (!Synapse) return;
        cleanup();
        setShowPreview(true);
        const sampleTask = await generateSampleTaskFromConfig(config);
        setSampleTask(sampleTask);

        setTimeout(() => {
          sfInstance.current = new Synapse(rootRef.current, {
            config,
            task: sampleTask,
            interfaces,
            instanceOptions: {
              reactVersion: "v18",
            },
            settings: {
              forceBottomPanel: true,
              collapsibleBottomPanel: true,
              // Default collapsed in all,preview-inline, but not in preview
              defaultCollapsedBottomPanel: displayMode !== "preview",
              fullscreen: false,
            },
            onStorageInitialized: (LS: any) => {
              const initAnnotation = () => {
                const as = LS.annotationStore;
                const c = as.createAnnotation();
                as.selectAnnotation(c.id);

                const annotation = as.selected;
                if (annotation) {
                  snapshotDisposer = onSnapshot(annotation, () => {
                    setAnnotation(annotation.serializeAnnotation());
                  });
                }
              };
              setTimeout(initAnnotation);
            },
          });
        });
      }

      if (!loading && !error && config) {
        rafId.current = requestAnimationFrame(() => {
          loadSF();
        });
      }

      return () => {
        cleanup();
      };
      // eslint-disable-next-line
    }, [config, loading, error, interfaces, onAnnotationUpdate]);

    return (
      <div className="h-full flex flex-col min-h-0">
        {error ? (
          <div className="text-danger-foreground text-body-medium flex-1 flex items-center justify-center">{error}</div>
        ) : loading ? (
          <div className="text-secondary-foreground text-body-medium flex-1 flex items-center justify-center">
            Loading config...
          </div>
        ) : showPreview ? (
          <div ref={rootRef} className="w-full h-full flex-1 min-h-0 flex flex-col" />
        ) : null}
      </div>
    );
  },
  () => true,
);

