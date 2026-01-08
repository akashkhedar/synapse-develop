/** @global SF * /

/**
 * @typedef {{
 *  hiddenColumns?: {
 *    labeling?: string[],
 *    explore?: string[],
 *  },
 *  visibleColumns?: {
 *    labeling?: string[],
 *    explore?: string[],
 *  }
 * }} TableConfig
 */

/**
 * @typedef {{
 * root: HTMLElement,
 * polling: boolean,
 * apiGateway: string | URL,
 * apiEndpoints: import("../utils/api-proxy").Endpoints,
 * apiMockDisabled: boolean,
 * apiHeaders?: Dict<string>,
 * settings: Dict<any>,
 * Synapse: Dict<any>,
 * env: "development" | "production",
 * mode: "labelstream" | "explorer",
 * table: TableConfig,
 * links: Dict<string|null>,
 * showPreviews: boolean,
 * projectId?: number,
 * datasetId?: number,
 * interfaces: Dict<boolean>,
 * instruments: Dict<any>,
 * toolbar?: string,
 * spinner?: import("react").ReactNode
 * apiTransform?: Record<string, Record<string, Function>
 * tabControls?: { add?: boolean, delete?: boolean, edit?: boolean, duplicate?: boolean },
 * }} DMConfig
 */

import { inject, observer } from "mobx-react";
import { destroy } from "mobx-state-tree";
import { unmountComponentAtNode } from "react-dom";
import camelCase from "lodash/camelCase";
import { instruments } from "../components/DataManager/Toolbar/instruments";
import { APIProxy } from "../utils/api-proxy";
import { FF_LSDV_4620_3_ML, isFF } from "../utils/feature-flags";
import { objectToMap } from "../utils/helpers";
import { serializeJsonForUrl, deserializeJsonFromUrl } from "@synapse/core";
import { isDefined } from "../utils/utils";
import { APIConfig } from "./api-config";
import { createApp } from "./app-create";
import { SFWrapper } from "./sf-sdk";
import { taskToSFFormat } from "./sf-utils";

const DEFAULT_TOOLBAR =
  "actions columns filters ordering label-button loading-possum error-box | refresh import-button export-button density-toggle grid-size view-toggle";

const prepareInstruments = (instruments) => {
  const result = Object.entries(instruments).map(([name, builder]) => [
    name,
    builder({ inject, observer }),
  ]);

  return objectToMap(Object.fromEntries(result));
};

export class DataManager {
  /** @type {HTMLElement} */
  root = null;

  /** @type {APIProxy} */
  api = null;

  /** @type {import("./sf-sdk").SFWrapper} */
  sf = null;

  /** @type {Dict} */
  settings = {};

  /** @type {import("../stores/AppStore").AppStore} */
  store = null;

  /** @type {Dict<any>} */
  SynapseOptions = {};

  /** @type {"development" | "production"} */
  env = "development";

  /** @type {"explorer" | "labelstream"} */
  mode = "explorer";

  /** @type {TableConfig} */
  tableConfig = {};

  /** @type {Dict<string|null>} */
  links = {
    import: "/import",
    export: "/export",
    settings: "./settings",
  };

  /**
   * @private
   * @type {Map<String, Set<Function>>}
   */
  callbacks = new Map();

  /**
   * @private
   * @type {Map<String, Set<Function>>}
   */
  actions = new Map();

  /** @type {Number} */
  apiVersion = 1;

  /** @type {boolean} */
  showPreviews = false;

  /** @type {boolean} */
  polling = true;

  /** @type {boolean} */
  started = false;

  instruments = new Map();

  /**
   * @type {DMConfig.tabControls}
   */
  tabControls = {
    add: true,
    delete: true,
    edit: true,
    duplicate: true,
  };

  /** @type {"dm" | "labelops"} */
  type = "dm";

  /** @type {string} */
  role = null;

  /**
   * Constructor
   * @param {DMConfig} config
   */
  constructor(config) {
    this.root = config.root;
    this.project = config.project;
    this.projectId = config.projectId ?? this?.project?.id;
    this.dataset = config.dataset;
    this.datasetId = config.datasetId;
    this.settings = config.settings;
    this.SynapseOptions = config.Synapse;
    this.env = config.env ?? process.env.NODE_ENV ?? this.env;
    this.mode = config.mode ?? this.mode;
    this.tableConfig = config.table ?? {};
    this.apiVersion = config?.apiVersion ?? 1;
    this.links = Object.assign(this.links, config.links ?? {});
    this.showPreviews = config.showPreviews ?? false;
    this.polling = config.polling;
    this.toolbar = config.toolbar ?? DEFAULT_TOOLBAR;
    this.spinner = config.spinner;
    this.spinnerSize = config.spinnerSize;
    this.instruments = prepareInstruments(config.instruments ?? {});
    this.apiTransform = config.apiTransform ?? {};
    this.preload = config.preload ?? {};
    this.role = config.role ?? null;

    // Get canAnnotate from multiple sources
    // Priority: config.canAnnotate > window.APP_SETTINGS.user.can_annotate > config.Synapse.user.can_annotate > true
    const userCanAnnotate =
      window.APP_SETTINGS?.user?.can_annotate ??
      config.Synapse?.user?.can_annotate;
    this.canAnnotate = config.canAnnotate ?? userCanAnnotate ?? true;
    console.log(
      "🔍 DataManager constructor - canAnnotate:",
      this.canAnnotate,
      "sources:",
      {
        config: config.canAnnotate,
        appSettings: window.APP_SETTINGS?.user?.can_annotate,
        SynapseUser: config.Synapse?.user?.can_annotate,
        user: window.APP_SETTINGS?.user,
      }
    );

    this.interfaces = objectToMap({
      tabs: true,
      toolbar: true,
      import: true,
      export: true,
      labelButton: true,
      backButton: true,
      labelingHeader: true,
      groundTruth: false,
      instruction: false,
      autoAnnotation: false,
      ...config.interfaces,
    });

    this.api = new APIProxy(
      this.apiConfig({
        apiGateway: config.apiGateway,
        apiEndpoints: config.apiEndpoints,
        apiMockDisabled: config.apiMockDisabled,
        apiSharedParams: config.apiSharedParams,
        apiHeaders: config.apiHeaders,
      })
    );

    Object.assign(this.tabControls, config.tabControls ?? {});

    this.updateActions(config.actions);

    this.type = config.type ?? "dm";

    this.initApp();
  }

  get isExplorer() {
    return this.mode === "labeling";
  }

  get isLabelStream() {
    return this.mode === "labelstream";
  }

  get projectId() {
    return (this._projectId = this._projectId ?? this.root?.dataset?.projectId);
  }

  set projectId(value) {
    this._projectId = value;
  }

  apiConfig({
    apiGateway,
    apiEndpoints,
    apiMockDisabled,
    apiSharedParams,
    apiHeaders,
  }) {
    const config = Object.assign({}, APIConfig);

    config.gateway = apiGateway ?? config.gateway;
    config.mockDisabled = apiMockDisabled;
    config.commonHeaders = apiHeaders;

    Object.assign(config.endpoints, apiEndpoints ?? {});
    const sharedParams = {};

    if (!isNaN(this.projectId)) {
      sharedParams.project = this.projectId;
    }
    if (!isNaN(this.datasetId)) {
      sharedParams.dataset = this.datasetId;
    }
    Object.assign(config, {
      sharedParams: {
        ...sharedParams,
        ...(apiSharedParams ?? {}),
      },
    });

    return config;
  }

  /**
   * @param {import("../stores/Action.js").Action} action
   */
  addAction(action, callback) {
    const { id } = action;

    if (!id) throw new Error("Action must provide a unique ID");

    this.actions.set(id, { action, callback });

    const actions = Array.from(this.actions.values()).map(
      ({ action }) => action
    );

    this.store?.setActions(actions);
  }

  removeAction(id) {
    this.actions.delete(id);
    this.store.removeAction(id);
  }

  getAction(id) {
    return this.actions.get(id)?.callback;
  }

  installActions() {
    this.actions.forEach(({ action, callback }) => {
      this.addAction(action, callback);
    });
  }

  updateActions(actions) {
    if (!Array.isArray(actions)) return;

    actions.forEach(([action, callback]) => {
      if (!isDefined(action.id)) {
        throw new Error("Every action must provide a unique ID");
      }
      this.addAction(action, callback);
    });
  }

  registerInstrument(name, initializer) {
    if (instruments[name]) {
      return console.warn(`Can't override native instrument ${name}`);
    }

    this.instruments.set(
      name,
      initializer({
        store: this.store,
        observer,
        inject,
      })
    );

    this.store.updateInstruments();
  }

  /**
   * Assign an event handler
   * @param {string} eventName
   * @param {Function} callback
   */
  on(eventName, callback) {
    if (this.sf && eventName.startsWith("sf:")) {
      const evt = camelCase(eventName.replace(/^sf:/, ""));

      this.sf?.sfInstance?.on(evt, callback);
    }

    const events = this.getEventCallbacks(eventName);

    events.add(callback);
    this.callbacks.set(eventName, events);
  }

  /**
   * Remove an event handler
   * If no callback provided, all assigned callbacks will be removed
   * @param {string} eventName
   * @param {Function?} callback
   */
  off(eventName, callback) {
    if (this.sf && eventName.startsWith("sf:")) {
      const evt = camelCase(eventName.replace(/^sf:/, ""));

      this.sf?.sfInstance?.off(evt, callback);
    }

    const events = this.getEventCallbacks(eventName);

    if (callback) {
      events.delete(callback);
    } else {
      events.clear();
    }
  }

  removeAllListeners() {
    const sfEvents = Array.from(this.callbacks.keys()).filter((evt) =>
      evt.startsWith("sf:")
    );

    sfEvents.forEach((evt) => {
      const callbacks = Array.from(this.getEventCallbacks(evt));
      const eventName = camelCase(evt.replace(/^sf:/, ""));

      callbacks.forEach((clb) => this.sf?.sfInstance?.off(eventName, clb));
    });

    this.callbacks.clear();
  }

  /**
   * Check if an event has at least one handler
   * @param {string} eventName Name of the event to check
   */
  hasHandler(eventName) {
    return this.getEventCallbacks(eventName).size > 0;
  }

  /**
   * Check if interface is enabled
   * @param {string} name Name of the interface
   */
  interfaceEnabled(name) {
    return this.store.interfaceEnabled(name);
  }

  /**
   *
   * @param {"explorer" | "labelstream"} mode
   */
  setMode(mode) {
    const modeChanged = mode !== this.mode;

    this.mode = mode;
    this.store.setMode(mode);

    if (modeChanged) this.invoke("modeChanged", this.mode);
  }

  /**
   * Invoke handlers assigned to an event
   * @param {string} eventName
   * @param {any[]} args
   */
  async invoke(eventName, ...args) {
    if (eventName.startsWith("sf:")) return;

    this.getEventCallbacks(eventName).forEach((callback) =>
      callback.apply(this, args)
    );
  }

  /**
   * Get callbacks set for a particular event
   * @param {string} eventName
   */
  getEventCallbacks(eventName) {
    return this.callbacks.get(eventName) ?? new Set();
  }

  /** @private */
  async initApp() {
    this.store = await createApp(this.root, this);

    // Fetch user's whoami (unified) endpoint and persist `is_annotator`
    try {
      const response = await fetch("/api/whoami/", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
      });

      if (response.ok) {
        const userData = await response.json();
        // Annotators and experts can annotate, clients cannot
        this.canAnnotate =
          userData.is_annotator === true || userData.is_expert === true;
        this.isAnnotator = !!userData.is_annotator;
        this.isClient = !!userData.is_client;
        this.isExpert = !!userData.is_expert;
        // Expose on SDK for other app code
        this.SDK = this.SDK || {};
        this.SDK.canAnnotate = this.canAnnotate;
        this.SDK.isAnnotator = this.isAnnotator;
        this.SDK.isClient = this.isClient;
        this.SDK.isExpert = this.isExpert;

        console.log("✅ Fetched whoami:", {
          canAnnotate: this.canAnnotate,
          isAnnotator: this.isAnnotator,
          isClient: this.isClient,
          isExpert: this.isExpert,
          email: userData.email,
        });
      } else {
        console.warn(
          "⚠️ Failed to fetch /api/whoami/, defaulting canAnnotate to false"
        );
        this.SDK = this.SDK || {};
        this.SDK.canAnnotate = false;
        this.SDK.isAnnotator = false;
        this.SDK.isClient = false;
        this.SDK.isExpert = false;
      }
    } catch (error) {
      console.warn(
        "⚠️ Error fetching /api/whoami/:",
        error,
        "defaulting canAnnotate to false"
      );
      this.SDK = this.SDK || {};
      this.SDK.canAnnotate = false;
      this.SDK.isAnnotator = false;
      this.SDK.isClient = false;
      this.SDK.isExpert = false;
    }

    // SDK flags already set above; log them
    console.log("✅ DataManager.SDK flags:", {
      canAnnotate: this.SDK.canAnnotate,
      isAnnotator: this.SDK.isAnnotator,
      isClient: this.SDK.isClient,
      isExpert: this.SDK.isExpert,
    });

    this.invoke("ready", [this]);
  }

  initSF(element) {
    if (this.sf) return;

    this.sf = new SFWrapper(this, element, {
      ...this.SynapseOptions,
      task: this.store.taskStore.selected,
      preload: this.preload,
      // annotation: this.store.annotationStore.selected,
      isLabelStream: this.mode === "labelstream",
      canAnnotate: this.canAnnotate,
    });
  }

  /**
   * Initialize SF or use already initialized instance.
   * Render SF interface and load task for labeling.
   * @param {HTMLElement} element Root element SF will be rendered into
   * @param {import("../stores/Tasks").TaskModel} task
   */
  async startLabeling() {
    if (!this.sf) return;

    const [task, annotation] = [
      this.store.taskStore.selected,
      this.store.annotationStore.selected,
    ];

    const isLabelStream = this.mode === "labelstream";
    const taskExists = isDefined(this.sf.task) && isDefined(task);
    const taskSelected = this.sf.task?.id === task?.id;

    // do nothing if the task is already selected
    if (taskExists && taskSelected) {
      return;
    }

    if (!isLabelStream && (!taskSelected || isDefined(annotation))) {
      const annotationID = annotation?.id ?? task.lastAnnotation?.id;

      // this.sf.loadTask(task.id, annotationID);
      this.sf.selectTask(task, annotationID);
    }
  }

  destroySF() {
    this.invoke("beforeSfDestroy", this, this.sf?.sfInstance);
    this.sf?.destroy();
    this.sf = undefined;
  }

  destroy(detachCallbacks = true) {
    if (isFF(FF_LSDV_4620_3_ML)) {
      this.destroySF();
    }
    unmountComponentAtNode(this.root);

    if (this.store) {
      destroy(this.store);
    }

    if (detachCallbacks) {
      this.callbacks.forEach((callbacks) => callbacks.clear());
      this.callbacks.clear();
    }
  }

  reload() {
    this.destroy(false);
    this.initApp();
    this.installActions();
  }

  async apiCall(...args) {
    return this.store.apiCall(...args);
  }

  getInstrument(name) {
    return instruments[name] ?? this.instruments.get(name) ?? null;
  }

  hasInterface(name) {
    return this.interfaces.get(name) === true;
  }

  get toolbarInstruments() {
    const sections = this.toolbar.split("|").map((s) => s.trim());

    const instrumentsList = sections.map((section) => {
      return section.split(" ").filter((instrument) => {
        const nativeInstrument = !!instruments[instrument];
        const customInstrument = !!this.instruments.has(instrument);

        if (!nativeInstrument && !customInstrument) {
          console.warn(
            `Unknwown instrument detected: ${instrument}. Did you forget to register it?`
          );
        }

        return nativeInstrument || customInstrument;
      });
    });

    return instrumentsList;
  }
  static urlJSON = { serializeJsonForUrl, deserializeJsonFromUrl };
  static taskToSFFormat = taskToSFFormat;
}
