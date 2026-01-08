import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Spinner } from "../../../components";
import { cn } from "../../../utils/bem";
import "./Config.scss";
import { EMPTY_CONFIG } from "./Template";
import { API_CONFIG } from "../../../config/ApiConfig";
import { useAPI } from "../../../providers/ApiProvider";

const configClass = cn("configure");

// Lazy load Synapse with a single promise to avoid multiple loads
// and enable as early as possible to load the dependencies once this component is mounted for the first time
let dependencies;
const loadDependencies = async () => {
  if (!dependencies) {
    dependencies = import("@synapse/editor");
  }
  return dependencies;
};

export const Preview = ({ config, data, error, loading, project }) => {
  // @see comment about dependencies above
  loadDependencies();

  const [storeReady, setStoreReady] = useState(false);
  const sf = useRef(null);
  const rootRef = useRef();
  const api = useAPI();
  const projectRef = useRef(project);
  projectRef.current = project;

  const currentTask = useMemo(() => {
    return {
      id: 1,
      annotations: [],
      predictions: [],
      data,
    };
  }, [data]);

  /**
   * Proxy urls to presign them if storage is connected
   * @param {*} _ Synapse instance
   * @param {string} url http/https are not proxied and returned as is
   */
  const onPresignUrlForProject = async (_, url) => {
    // if URL is a relative, presigned url (url matches /tasks|projects/:id/resolve/.*) make it absolute
    const presignedUrlPattern = /^\/(?:tasks|projects)\/\d+\/resolve\/?/;
    if (presignedUrlPattern.test(url)) {
      url = new URL(url, document.location.origin).toString();
    }

    const parsedUrl = new URL(url);

    // return same url if http(s)
    if (["http:", "https:"].includes(parsedUrl.protocol)) return url;

    const projectId = projectRef.current.id;

    const fileuri = btoa(url);

    return api.api.createUrl(API_CONFIG.endpoints.presignUrlForProject, {
      projectId,
      fileuri,
    }).url;
  };

  const currentConfig = useMemo(() => {
    // empty string causes error in SF
    return config ?? EMPTY_CONFIG;
  }, [config]);

  const initSynapse = useCallback(async (config, task) => {
    // wait for dependencies to load, the promise is resolved only once
    // and is started when the component is mounted for the first time
    await loadDependencies();

    if (sf.current || !task.data) return;

    try {
      sf.current = new window.Synapse(rootRef.current, {
        config,
        task,
        interfaces: ["side-column"],
        // with SharedStore we should use more late event
        onStorageInitialized(LS) {
          LS.settings.bottomSidePanel = true;

          const initAnnotation = () => {
            const as = LS.annotationStore;
            const c = as.createAnnotation();

            as.selectAnnotation(c.id);
            setStoreReady(true);
          };

          // and even then we need to wait a little even after the store is initialized
          setTimeout(initAnnotation);
        },
      });

      sf.current.on("presignUrlForProject", onPresignUrlForProject);
    } catch (err) {
      console.error(err);
    }
  }, []);

  useEffect(() => {
    const opacity = loading || error ? 0.6 : 1;
    // to avoid rerenders and data loss we do it this way

    document.getElementById("synapse").style.opacity = opacity;
  }, [loading, error]);

  useEffect(() => {
    initSynapse(currentConfig, currentTask).then(() => {
      if (storeReady && sf.current?.store) {
        const store = sf.current.store;

        store.resetState();
        store.assignTask(currentTask);
        store.assignConfig(currentConfig);
        store.initializeStore(currentTask);

        const c = store.annotationStore.addAnnotation({
          userGenerate: true,
        });

        store.annotationStore.selectAnnotation(c.id);
        console.log("sf updated");
      }
    });
  }, [currentConfig, currentTask, storeReady]);

  useEffect(() => {
    return () => {
      if (sf.current) {
        console.info("Destroying SF");
        sf.current.destroy();
        sf.current = null;
      }
    };
  }, []);

  return (
    <div className={configClass.elem("preview")}>
      <h3>UI Preview</h3>
      {error && (
        <div className={configClass.elem("preview-error")}>
          <h2>
            {error.detail} {error.id}
          </h2>
          {error.validation_errors?.non_field_errors?.map?.((err) => (
            <p key={err}>{err}</p>
          ))}
          {error.validation_errors?.label_config?.map?.((err) => (
            <p key={err}>{err}</p>
          ))}
          {error.validation_errors?.map?.((err) => (
            <p key={err}>{err}</p>
          ))}
        </div>
      )}
      {!data && loading && (
        <Spinner style={{ width: "100%", height: "50vh" }} />
      )}
      <div
        id="synapse"
        className={configClass.elem("preview-ui")}
        ref={rootRef}
      />
    </div>
  );
};
