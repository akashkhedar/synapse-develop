import {
  FF_DEV_1752,
  FF_DEV_2186,
  FF_DEV_2887,
  FF_DEV_3034,
  FF_LSDV_4620_3_ML,
  FF_REGION_VISIBILITY_FROM_URL,
  isFF,
} from "../utils/feature-flags";
import { isDefined } from "../utils/utils";
import { Modal } from "../components/Common/Modal/Modal";
import { CommentsSdk } from "./comments-sdk";
// import { SFHistory } from "./sf-history";
import { annotationToServer, taskToSFFormat } from "./sf-utils";
import { when } from "mobx";
import { isAlive } from "mobx-state-tree";

const DEFAULT_INTERFACES = [
  "basic",
  "controls",
  "submit",
  "update",
  "predictions",
  "topbar",
  "predictions:menu", // right menu with prediction items
  "annotations:menu", // right menu with annotation items
  "annotations:current",
  "side-column", // entity
  "edit-history", // undo/redo
];

let SynapseDM;

const resolveSynapse = () => {
  if (SynapseDM) {
    return SynapseDM;
  }
  if (window.Synapse) {
    return (SynapseDM = window.Synapse);
  }
};

// Returns true to suppress (swallow) the error, false to bubble to global handler.
// We allow 403 PAUSED to bubble so the app-level ApiProvider can show the paused modal
const errorHandlerAllowPaused = (result) => {
  const isPaused =
    result?.status === 403 &&
    typeof result?.response === "object" &&
    result?.response?.display_context?.reason === "PAUSED";
  return !isPaused;
};

// Support portal URL constants used to construct error reporting links
// These are used in showOperationToast() to create support links with request IDs
// for better error tracking and customer support
export const SUPPORT_URL = "https://support.Synapse.com/hc/en-us/requests/new";
export const SUPPORT_URL_REQUEST_ID_PARAM = "tf_37934448633869"; // request_id field ID in ZD

export class SFWrapper {
  /** @type {HTMLElement} */
  root = null;

  /** @type {DataManager} */
  datamanager = null;

  /** @type {Task} */
  // `task` is exposed via a getter later in the class. Avoid declaring
  // an instance field with the same name because it prevents the getter
  // from functioning (assignment to a getter-only property error).

  /** @type {Annotation} */
  initialAnnotation = null;

  /** @type {Synapse} */
  sf = null;

  /** @type {SFHistory} */
  // history = null;

  /** @type {boolean} */
  labelStream = false;

  /** @type {boolean} */
  isInteractivePreannotations = false;

  /** @type {function} */
  interfacesModifier = (interfaces) => interfaces;

  /**
   *
   * @param {DataManager} dm
   * @param {HTMLElement} element
   * @param {SFOptions} options
   */
  constructor(dm, element, options) {
    // we need to pass the rest of the options to SF below
    const {
      task,
      preload,
      isLabelStream,
      annotation,
      interfacesModifier,
      isInteractivePreannotations,
      user,
      keymap,
      messages,
      canAnnotate,
      ...restOptions
    } = options;

    this.datamanager = dm;
    this.root = element;
    // Do not keep MST nodes on this wrapper — store only task id (primitive)
    this.taskId = task?.id ?? null;
    this.preload = preload;
    this.labelStream = isLabelStream ?? false;
    this.initialAnnotation = annotation;
    this.interfacesModifier = interfacesModifier;
    this.isInteractivePreannotations = isInteractivePreannotations ?? false;
    this.canAnnotate = canAnnotate ?? true;

    // Helper to resolve the live task node from the store when needed
    this.getTaskNode = () => {
      try {
        const store = this.datamanager?.store;
        if (!store || !isAlive(store)) return null;
        const taskStore = store.taskStore;
        if (!taskStore || !isAlive(taskStore)) return null;
        const list = taskStore.list ?? [];
        return list.find((t) => String(t.id) === String(this.taskId)) ?? null;
      } catch (e) {
        return null;
      }
    };

    console.log(
      "🔍 SFWrapper constructor - canAnnotate:",
      this.canAnnotate,
      "user:",
      user
    );

    let interfaces = [...DEFAULT_INTERFACES];

    if (this.project.enable_empty_annotation === false) {
      interfaces.push("annotations:deny-empty");
    }

    if (
      window.APP_SETTINGS.annotator_reviewer_firewall_enabled &&
      this.labelStream
    ) {
      interfaces.push("annotations:hide-info");
    }

    if (this.labelStream) {
      interfaces.push("infobar");
      if (!window.APP_SETTINGS.label_stream_navigation_disabled)
        interfaces.push("topbar:prevnext");
      if (
        FF_DEV_2186 &&
        this.project.review_settings?.require_comment_on_reject
      ) {
        interfaces.push("comments:update");
      }
      if (this.project.show_skip_button) {
        interfaces.push("skip");
      }
    } else {
      interfaces.push(
        "infobar",
        "annotations:add-new",
        "annotations:view-all",
        "annotations:delete",
        "annotations:tabs",
        "predictions:tabs"
      );
      if (isFF(FF_REGION_VISIBILITY_FROM_URL)) {
        interfaces.push("annotations:copy-link");
      }
    }

    if (this.datamanager.hasInterface("instruction")) {
      interfaces.push("instruction");
    }

    if (!this.labelStream && this.datamanager.hasInterface("groundTruth")) {
      interfaces.push("ground-truth");
    }

    if (this.datamanager.hasInterface("autoAnnotation")) {
      interfaces.push("auto-annotation");
    }

    if (isFF(FF_DEV_2887)) {
      interfaces.push("annotations:comments");
      interfaces.push("comments:resolve-any");
    }

    if (this.project.review_settings?.require_comment_on_reject) {
      interfaces.push("comments:reject");
    }

    if (this.interfacesModifier) {
      interfaces = this.interfacesModifier(interfaces, this.labelStream);
    }

    // Add expert-review interface if user is an expert viewing a task that needs review
    console.log("🔍 Expert review check:", {
      is_expert: user?.is_expert,
      has_consensus: !!task?.consensus,
      consensus_status: task?.consensus?.status,
      task_id: task?.id,
      user_email: user?.email,
    });

    // Experts can review any task assigned to them, regardless of consensus status
    if (user?.is_expert) {
      interfaces.push("expert-review");
      console.log(
        "🎯 Expert review mode enabled for task",
        task.id,
        "- User is expert"
      );

      if (task?.consensus) {
        console.log("✅ Task has consensus data:", task.consensus.status);
      } else {
        console.log(
          "⚠️ Task has no consensus data - buttons will still appear"
        );
      }
    } else {
      console.log("❌ User is not an expert - no review buttons");
    }

    if (!this.shouldLoadNext()) {
      interfaces = interfaces.filter((item) => {
        return !["topbar:prevnext", "skip"].includes(item);
      });
    }

    const queueTotal =
      dm.store.project.reviewer_queue_total || dm.store.project.queue_total;
    const queueDone = dm.store.project.queue_done;
    const queueLeft = dm.store.project.queue_left;
    const queuePosition = queueDone
      ? queueDone + 1
      : queueLeft
      ? queueTotal - queueLeft + 1
      : 1;
    const commentClassificationConfig =
      dm.store.project.comment_classification_config;

    const sfProperties = {
      user: options.user,
      config: this.sfConfig,
      task: taskToSFFormat(this.task),
      description: this.instruction,
      interfaces,
      users: dm.store.users.map((u) => u.toJSON()),
      keymap: options.keymap,
      forceAutoAnnotation: this.isInteractivePreannotations,
      forceAutoAcceptSuggestions: this.isInteractivePreannotations,
      messages: options.messages,
      queueTotal,
      queuePosition,
      commentClassificationConfig,
      // Enable readonly mode for org members
      readonlyAnnotation: !this.canAnnotate,

      /* EVENTS */
      // Disable annotation callbacks for read-only mode
      onSubmitDraft: this.canAnnotate ? this.onSubmitDraft : null,
      onSynapseLoad: this.onSynapseLoad,
      onTaskLoad: this.onTaskLoad,
      onPresignUrlForProject: this.onPresignUrlForProject,
      onStorageInitialized: this.onStorageInitialized,
      onSubmitAnnotation: this.canAnnotate ? this.onSubmitAnnotation : null,
      onUpdateAnnotation: this.canAnnotate ? this.onUpdateAnnotation : null,
      onDeleteAnnotation: this.canAnnotate ? this.onDeleteAnnotation : null,
      onSkipTask: this.canAnnotate ? this.onSkipTask : null,
      onUnskipTask: this.canAnnotate ? this.onUnskipTask : null,
      onGroundTruth: this.canAnnotate ? this.onGroundTruth : null,
      onEntityCreate: this.canAnnotate ? this.onEntityCreate : null,
      onEntityDelete: this.canAnnotate ? this.onEntityDelete : null,
      onSelectAnnotation: this.onSelectAnnotation,
      onNextTask: this.onNextTask,
      onPrevTask: this.onPrevTask,

      ...restOptions,
    };

    this.initSynapse(sfProperties);
  }

  /** @private */
  initSynapse(settings) {
    try {
      const Synapse = resolveSynapse();

      if (!Synapse) {
        console.error("Synapse library not loaded - window.Synapse is undefined");
        return;
      }

      this.sfInstance = new Synapse(this.root, settings);

      this.sfInstance.on("presignUrlForProject", this.onPresignUrlForProject);

      const names = Array.from(this.datamanager.callbacks.keys()).filter((k) =>
        k.startsWith("sf:")
      );

      names.forEach((name) => {
        this.datamanager.getEventCallbacks(name).forEach((clb) => {
          this.sfInstance.on(name.replace(/^sf:/, ""), clb);
        });
      });

      if (isFF(FF_DEV_2887)) {
        new CommentsSdk(this.sfInstance, this.datamanager);
      }

      this.datamanager.invoke("sfInit", this, this.sfInstance);
    } catch (err) {
      console.error("Failed to initialize Synapse", settings);
      console.error(err);
    }
  }

  /** @private */
  async preloadTask() {
    const { comment: commentId, task: taskID } = this.preload;
    const api = this.datamanager.api;
    const params = { taskID };

    if (commentId) {
      params.with_comment = commentId;
    }

    if (params) {
      const task = await api.call("task", { params });
      const noData =
        !task || (!task.annotations?.length && !task.drafts?.length);
      const body = `Task #${taskID}${
        commentId ? ` with comment #${commentId}` : ""
      } was not found!`;

      if (noData) {
        Modal.modal({
          title: "Can't find task",
          body,
        });
        return false;
      }

      // for preload it's good to always load the first one
      const annotation = task.annotations[0];

      this.selectTask(task, annotation?.id, true);
    }

    return false;
  }

  /** @private */
  async loadTask(taskID, annotationID, fromHistory = false) {
    if (!this.sf) {
      return console.error("Make sure that SF was properly initialized");
    }

    const nextAction = async () => {
      const tasks = this.datamanager.store.taskStore;

      const newTask = await this.withinLoadingState(async () => {
        let nextTask;

        if (!isDefined(taskID)) {
          nextTask = await tasks.loadNextTask();
        } else {
          nextTask = await tasks.loadTask(taskID);
        }

        /**
         * If we're in label stream and there's no task – end the stream
         * Otherwise allow user to continue exploring tasks after finished labelling
         */
        const noTask = this.labelStream && !nextTask;

        this.sf.setFlags({ noTask });

        return nextTask;
      });

      // Add new data from received task
      if (newTask) this.selectTask(newTask, annotationID, fromHistory);
    };

    if (isFF(FF_DEV_2887) && this.sf?.commentStore?.hasUnsaved) {
      Modal.confirm({
        title: "You have unsaved changes",
        body: "There are comments which are not persisted. Please submit the annotation. Continuing will discard these comments.",
        onOk() {
          nextAction();
        },
        okText: "Discard and continue",
      });
      return;
    }

    await nextAction();
  }

  exitStream() {
    this.datamanager.invoke("navigate", "projects");
  }

  selectTask(task, annotationID, fromHistory = false) {
    const incomingId = task?.id ?? null;
    const needsAnnotationsMerge = task && this.taskId === incomingId;
    const annotations = needsAnnotationsMerge ? [...this.annotations] : [];

    // update stored primitive id only
    this.taskId = incomingId;

    if (needsAnnotationsMerge) {
      const node = this.getTaskNode();
      if (node && isAlive(node)) {
        try {
          node.mergeAnnotations(annotations);
        } catch (e) {
          console.warn("[SFWrapper] mergeAnnotations failed:", e);
        }
      }
    }

    this.loadUserLabels();

    this.setSFTask(task, annotationID, fromHistory);
  }

  setSFTask(task, annotationID, fromHistory, selectPrediction = false) {
    if (!this.sf) return;

    const hasChangedTasks = this.sf?.task?.id !== task?.id && task?.id;

    this.setLoading(true, hasChangedTasks);
    const sfTask = taskToSFFormat(task);
    const isRejectedQueue = isDefined(task.default_selected_annotation);
    const taskList = this.datamanager.store.taskStore.list;
    // annotations are set in SF only and order in DM only, so combine them
    const taskHistory = taskList
      .map((task) => this.taskHistory.find((item) => item.taskId === task.id))
      .filter(Boolean);

    const extracted = taskHistory.find((item) => item.taskId === task.id);

    if (!fromHistory && extracted) {
      taskHistory.splice(taskHistory.indexOf(extracted), 1);
      taskHistory.push(extracted);
    }

    if (!extracted) {
      taskHistory.push({ taskId: task.id, annotationId: null });
    }

    if (isRejectedQueue && !annotationID) {
      annotationID = task.default_selected_annotation;
    }

    if (hasChangedTasks) {
      // Always reset state for changed tasks to ensure clean render
      // This fixes blank canvas issues with ZIP files
      this.sf.resetState();
    } else {
      this.sf.resetAnnotationStore();
    }

    // Initial idea to show counter for Manual assignment only
    // But currently we decided to hide it for any stream
    // const distribution = this.project.assignment_settings.label_stream_task_distribution;
    // const isManuallyAssigned = distribution === "assigned_only";

    // undefined or true for backward compatibility
    this.sf.toggleInterface("postpone", task.allow_postpone !== false);
    this.sf.toggleInterface("topbar:task-counter", true);
    this.sf.assignTask(task);
    this.sf.initializeStore(sfTask);
    this.setAnnotation(
      annotationID,
      fromHistory || isRejectedQueue,
      selectPrediction
    );
    this.setLoading(false);
  }

  /** @private */
  setAnnotation(
    annotationID,
    selectAnnotation = false,
    selectPrediction = false
  ) {
    if (!this.sf) {
      console.warn("[SFWrapper] setAnnotation called but sf is not initialized");
      return;
    }
    const id = annotationID ? annotationID.toString() : null;
    const { annotationStore: cs } = this.sf;
    let annotation;
    const activeDrafts = cs.annotations.map((a) => a.draftId).filter(Boolean);

    const taskNode = this.getTaskNode();
    if (taskNode && isAlive(taskNode) && taskNode.drafts) {
      for (const draft of taskNode.drafts) {
        if (activeDrafts.includes(draft.id)) continue;
        let c;

        if (draft.annotation) {
          const draftAnnotationPk = String(draft.annotation);

          c = cs.annotations.find((c) => c.pk === draftAnnotationPk);
          if (c) {
            c.history.freeze();
            c.addVersions({ draft: draft.result });
            c.deleteAllRegions({ deleteReadOnly: true });
          } else {
            // that shouldn't happen
            console.error(`No annotation found for pk=${draftAnnotationPk}`);
            continue;
          }
        } else {
          // Annotation not found - restore annotation from draft
          c = cs.addAnnotation({
            draft: draft.result,
            userGenerate: true,
            comment_count: draft.comment_count,
            unresolved_comment_count: draft.unresolved_comment_count,
            createdBy: draft.created_username,
            createdAgo: draft.created_ago,
            createdDate: draft.created_at,
          });
        }
        cs.selectAnnotation(c.id);
        c.deserializeResults(draft.result);
        c.setDraftId(draft.id);
        c.setDraftSaved(draft.created_at);
        c.history.safeUnfreeze();
        c.history.reinit();
      }
    }
    const first = this.annotations?.length ? this.annotations[0] : null;
    // if we have annotations created automatically, we don't need to create another one
    // automatically === created here and haven't saved yet, so they don't have pk
    // @todo because of some weird reason pk may be string uid, so check flags then
    const hasAutoAnnotations =
      !!first &&
      (!first.pk || (first.userGenerate && first.sentUserGenerate === false));
    const showPredictions = this.project.show_collab_predictions === true;

    if (this.labelStream) {
      if (first?.draftId) {
        // not submitted draft, most likely from previous labeling session
        annotation = first;
      } else if (isDefined(annotationID) && selectAnnotation) {
        annotation = this.annotations.find(({ pk }) => pk === annotationID);
      } else if (
        showPredictions &&
        this.predictions.length > 0 &&
        !this.isInteractivePreannotations
      ) {
        annotation = cs.addAnnotationFromPrediction(this.predictions[0]);
      } else {
        annotation = cs.createAnnotation();
      }
    } else {
      if (selectPrediction) {
        annotation = this.predictions.find((p) => p.pk === id);
        annotation ??= first; // if prediction not found, select first annotation and resume existing behaviour
      } else if (
        this.annotations.length === 0 &&
        this.predictions.length > 0 &&
        !this.isInteractivePreannotations
      ) {
        annotation = cs.addAnnotationFromPrediction(this.predictions[0]);
      } else if (this.annotations.length > 0 && id && id !== "auto") {
        annotation = this.annotations.find((c) => c.pk === id || c.id === id);
      } else if (
        this.annotations.length > 0 &&
        (id === "auto" || hasAutoAnnotations)
      ) {
        annotation = first;
      } else {
        annotation = cs.createAnnotation();
      }
    }

    if (annotation) {
      // We want to be sure this is explicitly understood to be a prediction and the
      // user wants to select it directly
      if (selectPrediction && annotation.type === "prediction") {
        cs.selectPrediction(annotation.id);
      } else {
        // Otherwise we default the behaviour to being as was before
        cs.selectAnnotation(annotation.id);
      }
      this.datamanager.invoke("annotationSet", annotation);
    }
  }

  saveUserLabels = async () => {
    const body = [];
    const userLabels = this.sf?.userLabels?.controls;

    if (!userLabels) return;

    for (const from_name in userLabels) {
      for (const label of userLabels[from_name]) {
        body.push({
          value: label.path,
          title: [from_name, JSON.stringify(label.path)].join(":"),
          from_name,
          project: this.project.id,
        });
      }
    }

    if (!body.length) return;

    await this.datamanager.apiCall("saveUserLabels", {}, { body });
  };

  async loadUserLabels() {
    // Avoid directly accessing `this.sf.userLabels` synchronously because
    // that property may create observables during Synapse's init phase
    // which leads to MST assertion errors. Instead, probe it inside try/catch
    // and retry a few times before giving up.

    const canAccessUserLabels = () => {
      try {
        if (!this.sf) return false;
        // Ensure datamanager store is alive to avoid accessing MST getters on dead tree
        if (
          !this.datamanager ||
          !this.datamanager.store ||
          !isAlive(this.datamanager.store)
        )
          return false;
        // Use `in` operator to check property existence without invoking its getter
        if (!("userLabels" in this.sf)) return false;
        return true;
      } catch (err) {
        return false;
      }
    };

    // Wait for `userLabels` to become accessible (up to ~500ms)
    const maxAttempts = 10;
    const delayMs = 50;
    let attempts = 0;
    while (!canAccessUserLabels() && attempts < maxAttempts) {
      // small delay
      // eslint-disable-next-line no-await-in-loop
      await new Promise((r) => setTimeout(r, delayMs));
      attempts += 1;
    }

    if (!canAccessUserLabels()) {
      console.warn(
        "[SFWrapper] userLabels not available after waiting; skipping init"
      );
      return;
    }

    let userLabels;
    try {
      userLabels = await this.datamanager.apiCall("userLabelsForProject", {
        project: this.project.id,
        expand: "label",
      });
    } catch (err) {
      console.warn("[SFWrapper] userLabels API failed:", err);
      return;
    }

    if (!userLabels) return;

    const controls = {};

    for (const result of userLabels.results ?? []) {
      // don't trust server's response!
      if (!result?.label?.value?.length) continue;

      const control = result.from_name;

      if (!controls[control]) controls[control] = [];
      controls[control].push(result.label.value);
    }

    // Schedule init on next tick and guard with try/catch to avoid MST initialization errors
    return new Promise((resolve) => {
      const tryInit = async () => {
        try {
          if (!this.sf || !this.sf.userLabels) return;

          // If the userLabels has an `isInitializing` flag, wait until it's false (or timeout)
          try {
            if (typeof this.sf.userLabels.isInitializing !== "undefined") {
              await Promise.race([
                when(() => this.sf.userLabels.isInitializing === false),
                new Promise((r) => setTimeout(r, 500)),
              ]);
            }
          } catch (e) {
            // ignore when/timeout errors
          }

          if (this.sf.userLabels.init) {
            try {
              this.sf.userLabels.init(controls);
            } catch (err) {
              console.warn("[SFWrapper] userLabels.init failed:", err);
            }
          }
        } catch (err) {
          console.warn("[SFWrapper] userLabels init guard failed:", err);
        } finally {
          resolve();
        }
      };

      setTimeout(tryInit, 0);
    });
  }

  onSynapseLoad = async (ls) => {
    console.log("[SFWrapper] onSynapseLoad called with:", ls);
    
    // Guard: if datamanager store was destroyed/removed, skip Synapse load handling
    if (
      !this.datamanager ||
      !this.datamanager.store ||
      !isAlive(this.datamanager.store)
    ) {
      console.warn(
        "[SFWrapper] datamanager.store not alive onSynapseLoad; skipping initialization"
      );
      return;
    }

    this.datamanager.invoke("SynapseLoad", ls);
    this.sf = ls;
    console.log("[SFWrapper] this.sf is now set to:", this.sf);

    if (!this.sf.task) this.setLoading(true);

    // Hide label buttons for organization members who cannot annotate
    if (!this.canAnnotate) {
      const style = document.createElement("style");
      style.id = "hide-annotation-controls";
      style.textContent = `
        /* Hide label/choice buttons at the bottom */
        .sf-object-tag,
        .sf-labels,
        .sf-choices,
        [class*="Labels_"],
        [class*="Choices_"],
        [class*="ObjectTag_"],
        [data-testid="labels-list"],
        [data-testid="choices-list"] {
          display: none !important;
        }
        
        /* Disable canvas interactions */
        canvas,
        .konvajs-content {
          pointer-events: none !important;
        }
        
        /* Hide submit/update buttons */
        button[aria-label="submit"],
        button[aria-label="update"],
        [class*="Actions_"] button:not([class*="navigation"]) {
          display: none !important;
        }
        
        /* Replace instruction text with "View Annotation" */
        .sf-description,
        [class*="Description_"],
        .sf-header {
          visibility: hidden !important;
          position: relative !important;
        }
        
        .sf-description::after,
        [class*="Description_"]::after,
        .sf-header::after {
          content: "View Annotation" !important;
          visibility: visible !important;
          position: absolute !important;
          left: 0 !important;
          top: 0 !important;
          font-size: 18px !important;
          font-weight: 500 !important;
          color: #374151 !important;
        }
      `;
      document.head.appendChild(style);
      console.log(
        '🔒 Organization member: Label buttons hidden, text changed to "View Annotation"'
      );
    }

    const _taskHistory = await this.datamanager.store.taskStore.loadTaskHistory(
      {
        projectId: this.datamanager.store.project.id,
      }
    );

    // Normalize taskHistory to plain snapshots (avoid passing MST nodes)
    try {
      const safeHistory = Array.isArray(_taskHistory)
        ? _taskHistory.map((t) => {
            return {
              taskId: t?.taskId ?? null,
              annotationId:
                t?.annotationId != null ? String(t.annotationId) : null,
            };
          })
        : [];

      // Attempt to set task history; if Synapse's store is dead this may throw
      try {
        this.sf.setTaskHistory(safeHistory);
      } catch (err) {
        console.warn("[SFWrapper] setTaskHistory failed, skipping:", err);
      }
    } catch (e) {
      // Fallback: set original
      try {
        this.sf.setTaskHistory(_taskHistory);
      } catch (err) {
        console.warn("[SFWrapper] setTaskHistory fallback failed:", err);
      }
    }

    await this.loadUserLabels();

    if (this.canPreloadTask && isFF(FF_DEV_1752)) {
      await this.preloadTask();
    } else if (this.labelStream) {
      await this.loadTask();
    }

    this.setLoading(false);
  };

  /** @private */
  onTaskLoad = async (...args) => {
    this.datamanager.invoke("onSelectAnnotation", ...args);
  };

  /**
   * Proxy urls to presign them if storage is connected
   * @param {*} _ LS instance
   * @param {string} url http/https are not proxied and returned as is
   */
  onPresignUrlForProject = (_, url) => {
    // if URL is a relative, presigned url (url matches /tasks|projects/:id/resolve/.*) make it absolute
    const presignedUrlPattern = /^\/(?:tasks|projects)\/\d+\/resolve\/?/;
    if (presignedUrlPattern.test(url)) {
      url = new URL(url, document.location.origin).toString();
    }

    const parsedUrl = new URL(url);

    // return same url if http(s)
    if (["http:", "https:"].includes(parsedUrl.protocol)) return url;

    const api = this.datamanager.api;
    const projectId = this.project.id;
    const fileuri = btoa(url);

    return api.createUrl(api.endpoints.presignUrlForProject, {
      projectId,
      fileuri,
    }).url;
  };

  onStorageInitialized = async (ls) => {
    this.datamanager.invoke("onStorageInitialized", ls);

    if (this.labelStream === false && this.sf) {
      const node = this.getTaskNode();
      if (node && isAlive(node)) {
        const annotationID =
          this.initialAnnotation?.pk ??
          node.lastAnnotation?.pk ??
          node.lastAnnotation?.id ??
          "auto";

        this.setAnnotation(annotationID);
      }
    }
  };

  /** @private */
  showOperationToast(status, successMessage, errorAction, result) {
    if (status === 200 || status === 201) {
      this.datamanager.invoke("toast", {
        message: successMessage,
        type: "info",
      });
    } else if (status !== undefined) {
      const requestId = result?.$meta?.headers?.get("x-ls-request-id");
      const supportUrl = requestId
        ? `${SUPPORT_URL}?${SUPPORT_URL_REQUEST_ID_PARAM}=${requestId}`
        : SUPPORT_URL;

      this.datamanager.invoke("toast", {
        message: (
          <span>
            {errorAction}, please try again or{" "}
            <a
              href={supportUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "inherit", textDecoration: "underline" }}
              onClick={(e) => e.stopPropagation()}
            >
              contact our team
            </a>{" "}
            if it doesn't help.
          </span>
        ),
        type: "error",
      });
    }
  }

  /** @private */
  onSubmitAnnotation = async () => {
    const exitStream = this.shouldExitStream();
    const loadNext = exitStream ? false : this.shouldLoadNext();
    const result = await this.submitCurrentAnnotation(
      "submitAnnotation",
      async (taskID, body) => {
        return await this.datamanager.apiCall(
          "submitAnnotation",
          { taskID },
          { body },
          // errors are displayed by "toast" event - we don't want to show blocking modal
          { errorHandler: errorHandlerAllowPaused }
        );
      },
      false,
      loadNext
    );
    const status = result?.$meta?.status;

    this.showOperationToast(
      status,
      "Annotation saved successfully",
      "Annotation is not saved",
      result
    );

    if (exitStream) return this.exitStream();
  };

  /** @private */
  onUpdateAnnotation = async (ls, annotation, extraData) => {
    const { task } = this;
    const serializedAnnotation = this.prepareData(annotation);
    const exitStream = this.shouldExitStream();

    Object.assign(serializedAnnotation, extraData);

    await this.saveUserLabels();

    const result = await this.withinLoadingState(async () => {
      return this.datamanager.apiCall(
        "updateAnnotation",
        {
          taskID: task.id,
          annotationID: annotation.pk,
        },
        {
          body: serializedAnnotation,
        },
        // errors are displayed by "toast" event - we don't want to show blocking modal
        { errorHandler: errorHandlerAllowPaused }
      );
    });
    const status = result?.$meta?.status;

    this.showOperationToast(
      status,
      "Annotation updated successfully",
      "Annotation is not updated",
      result
    );

    this.datamanager.invoke("updateAnnotation", ls, annotation, result);

    if (exitStream) return this.exitStream();

    if (status >= 400) {
      return;
    }

    const isRejectedQueue = isDefined(task.default_selected_annotation);

    if (isRejectedQueue) {
      // load next task if that one was updated task from rejected queue
      await this.loadTask();
    } else {
      await this.loadTask(this.task.id, annotation.pk, true);
    }
  };

  deleteDraft = async (id) => {
    const response = await this.datamanager.apiCall("deleteDraft", {
      draftID: id,
    });

    this.task.deleteDraft(id);
    return response;
  };

  /**@private */
  onDeleteAnnotation = async (ls, annotation) => {
    const { task } = this;
    let response;

    task.deleteAnnotation(annotation);

    if (annotation.userGenerate && annotation.sentUserGenerate === false) {
      if (annotation.draftId) {
        response = await this.deleteDraft(annotation.draftId);
      } else {
        response = { ok: true };
      }
    } else {
      response = await this.withinLoadingState(async () => {
        return this.datamanager.apiCall("deleteAnnotation", {
          taskID: task.id,
          annotationID: annotation.pk,
        });
      });

      // this.task.deleteAnnotation(annotation);
      this.datamanager.invoke("deleteAnnotation", ls, annotation);
    }

    if (response.ok) {
      const lastAnnotation =
        this.annotations[this.annotations.length - 1] ?? {};
      const annotationID = lastAnnotation.pk ?? undefined;

      this.setAnnotation(annotationID);
    }
  };

  draftToast = (status, result = null) => {
    this.showOperationToast(
      status,
      "Draft saved successfully",
      "Draft is not saved",
      result
    );
  };

  needsDraftSave = (annotation) => {
    if (annotation.history?.hasChanges && !annotation.draftSaved) return true;
    if (
      annotation.history?.hasChanges &&
      new Date(annotation.history.lastAdditionTime) >
        new Date(annotation.draftSaved)
    )
      return true;
    return false;
  };

  saveDraft = async (target = null) => {
    const selected = target || this.sf?.annotationStore?.selected;
    const hasChanges = selected ? this.needsDraftSave(selected) : false;

    if (selected?.isDraftSaving) {
      await when(() => !selected.isDraftSaving);
      this.draftToast(200);
    } else if (hasChanges && selected) {
      const res = await selected?.saveDraftImmediatelyWithResults();

      this.draftToast(res.$meta?.status, res);
    }
  };

  onSubmitDraft = async (studio, annotation, params = {}) => {
    // It should be preserved as soon as possible because each `await` will allow it to be changed
    const taskId = this.task.id;
    const annotationDoesntExist = !annotation.pk;
    const data = { body: this.prepareData(annotation, { isNewDraft: true }) }; // serializedAnnotation
    const hasChanges = this.needsDraftSave(annotation);
    const showToast = params?.useToast && hasChanges;
    // console.log('onSubmitDraft', params?.useToast, hasChanges);

    if (params?.useToast) delete params.useToast;

    Object.assign(data.body, params);

    await this.saveUserLabels();

    if (annotation.draftId > 0) {
      // draft has been already created
      const res = await this.datamanager.apiCall(
        "updateDraft",
        { draftID: annotation.draftId },
        data
      );

      showToast && this.draftToast(res.$meta?.status, res);
      return res;
    }
    let response;

    if (annotationDoesntExist) {
      response = await this.datamanager.apiCall(
        "createDraftForTask",
        { taskID: taskId },
        data
      );
    } else {
      response = await this.datamanager.apiCall(
        "createDraftForAnnotation",
        { taskID: taskId, annotationID: annotation.pk },
        data
      );
    }
    response?.id && annotation.setDraftId(response?.id);
    showToast && this.draftToast(response.$meta?.status, response);

    return response;
  };

  onSkipTask = async (_, { comment } = {}) => {
    // Manager roles that can force-skip unskippable tasks (OW=Owner, AD=Admin, MA=Manager)
    const MANAGER_ROLES = ["OW", "AD", "MA"];
    const task = this.task;
    const taskAllowSkip = task?.allow_skip !== false;
    const userRole = window.APP_SETTINGS?.user?.role;
    const hasForceSkipPermission = MANAGER_ROLES.includes(userRole);
    const canSkip = taskAllowSkip || hasForceSkipPermission;
    if (!canSkip) {
      console.warn(
        "Task cannot be skipped: allow_skip is false and user lacks manager role"
      );
      this.showOperationToast(400, null, "This task cannot be skipped", {
        error: "Task cannot be skipped",
      });
      return;
    }
    const result = await this.submitCurrentAnnotation(
      "skipTask",
      async (taskID, body) => {
        const { id, ...annotation } = body;
        const params = { taskID };
        const options = { body: { ...annotation, was_cancelled: true } };

        if (comment) options.body.comment = comment;

        if (id !== undefined) params.annotationID = id;

        return await this.datamanager.apiCall(
          id === undefined ? "submitAnnotation" : "updateAnnotation",
          params,
          options,
          { errorHandler: errorHandlerAllowPaused }
        );
      },
      true,
      this.shouldLoadNext()
    );
    const status = result?.$meta?.status;

    this.showOperationToast(
      status,
      "Task skipped successfully",
      "Task is not skipped",
      result
    );
  };

  onUnskipTask = async () => {
    const { task, currentAnnotation } = this;

    if (!isDefined(currentAnnotation) && !isDefined(currentAnnotation.pk)) {
      console.error("Annotation must be on unskip");
      return;
    }

    await this.withinLoadingState(async () => {
      currentAnnotation.pauseAutosave();

      if (isFF(FF_DEV_3034)) {
        await this.datamanager.apiCall("convertToDraft", {
          annotationID: currentAnnotation.pk,
        });
      } else {
        if (currentAnnotation.draftId > 0) {
          await this.datamanager.apiCall(
            "updateDraft",
            {
              draftID: currentAnnotation.draftId,
            },
            {
              body: { annotation: null },
            }
          );
        } else {
          const annotationData = { body: this.prepareData(currentAnnotation) };

          await this.datamanager.apiCall(
            "createDraftForTask",
            {
              taskID: this.task.id,
            },
            annotationData
          );
        }

        // Carry over any comments to when the annotation draft is eventually submitted
        if (isFF(FF_DEV_2887) && this.sf?.commentStore?.toCache) {
          this.sf.commentStore.toCache(`task.${task.id}`);
        }

        await this.datamanager.apiCall("deleteAnnotation", {
          taskID: task.id,
          annotationID: currentAnnotation.pk,
        });
      }
    });
    await this.loadTask(task.id);
    this.datamanager.invoke("unskipTask");
  };

  shouldLoadNext = () => {
    if (!this.labelStream) return false;

    // validating if URL is from notification, in case of notification it shouldn't load next task
    const urlParam = new URLSearchParams(location.search).get("interaction");

    return urlParam !== "notifications";
  };

  shouldExitStream = () => {
    const paramName = "exitStream";
    const urlParam = new URLSearchParams(location.search).get(paramName);
    const searchParams = new URLSearchParams(window.location.search);

    searchParams.delete(paramName);
    let newRelativePathQuery = window.location.pathname;

    if (searchParams.toString())
      newRelativePathQuery += `?${searchParams.toString()}`;
    window.history.pushState(null, "", newRelativePathQuery);
    return !!urlParam;
  };

  // Proxy events that are unused by DM integration
  onEntityCreate = (...args) =>
    this.datamanager.invoke("onEntityCreate", ...args);
  onEntityDelete = (...args) =>
    this.datamanager.invoke("onEntityDelete", ...args);
  onSelectAnnotation = (prevAnnotation, nextAnnotation, options) => {
    if (window.APP_SETTINGS.read_only_quick_view_enabled && !this.labelStream) {
      prevAnnotation?.setEditable(false);
    }
    if (nextAnnotation?.history?.undoIdx) {
      this.saveDraft(nextAnnotation).then(() => {
        this.datamanager.invoke(
          "onSelectAnnotation",
          prevAnnotation,
          nextAnnotation,
          options,
          this
        );
      });
    } else {
      this.datamanager.invoke(
        "onSelectAnnotation",
        prevAnnotation,
        nextAnnotation,
        options,
        this
      );
    }
  };

  onNextTask = async (nextTaskId, nextAnnotationId) => {
    this.saveDraft();
    this.loadTask(nextTaskId, nextAnnotationId, true);
  };
  onPrevTask = async (prevTaskId, prevAnnotationId) => {
    this.saveDraft();
    this.loadTask(prevTaskId, prevAnnotationId, true);
  };
  async submitCurrentAnnotation(
    eventName,
    submit,
    includeId = false,
    loadNext = true
  ) {
    const { taskID, currentAnnotation } = this;
    const taskNode = this.getTaskNode();
    const unique_id = taskNode?.unique_lock_id;
    const serializedAnnotation = this.prepareData(currentAnnotation, {
      includeId,
    });

    if (unique_id) {
      serializedAnnotation.unique_id = unique_id;
    }

    this.setLoading(true);

    await this.saveUserLabels();

    const result = await this.withinLoadingState(async () => {
      const result = await submit(taskID, serializedAnnotation);

      return result;
    });

    if (result && result.id !== undefined) {
      const annotationId = result.id.toString();

      currentAnnotation.updatePersonalKey(annotationId);

      const eventData = annotationToServer(currentAnnotation);

      this.datamanager.invoke(eventName, this.sf, eventData, result);

      // Persist any queued comments which are not currently attached to an annotation
      if (
        isFF(FF_DEV_2887) &&
        ["submitAnnotation", "skipTask"].includes(eventName) &&
        this.sf?.commentStore?.persistQueuedComments
      ) {
        await this.sf.commentStore.persistQueuedComments();
      }
    }

    this.setLoading(false);
    if (result?.$meta?.status >= 400) {
      // don't reload the task on error to avoid losing the user's changes
      return result;
    }

    if (!loadNext || this.datamanager.isExplorer) {
      await this.loadTask(taskID, currentAnnotation.pk, true);
    } else {
      await this.loadTask();
    }

    return result;
  }

  /**
   * Finds the active draft for the given annotation.
   * @param {Object} annotation - The annotation object.
   * @returns {Object|undefined} The active draft or undefined if no draft is found.
   * @private
   */
  findActiveDraft(annotation) {
    if (isDefined(annotation.draftId)) {
      return this.task.drafts.find(
        (possibleDraft) => possibleDraft.id === annotation.draftId
      );
    }
    return undefined;
  }

  /**
   * Calculates the startedAt time for an annotation.
   * @param {Object|undefined} currentDraft - The current draft object, if any.
   * @param {Date} loadedDate - The date when the annotation was loaded.
   * @returns {Date} The calculated startedAt time.
   * @private
   */
  calculateStartedAt(currentDraft, loadedDate) {
    if (currentDraft) {
      const draftStartedAt = new Date(currentDraft.created_at);
      const draftLeadTime = Number(currentDraft.lead_time ?? 0);
      const adjustedStartedAt = new Date(Date.now() - draftLeadTime * 1000);

      if (adjustedStartedAt < draftStartedAt) return draftStartedAt;

      return adjustedStartedAt;
    }
    return loadedDate;
  }

  /**
   * Prepare data for draft/submission of annotation
   * @param {Object} annotation - The annotation object.
   * @param {Object} options - The options object.
   * @param {boolean} options.includeId - Whether to include the id in the result.
   * @param {boolean} options.isNewDraft - Whether the draft is new.
   * @returns {Object} The prepared data.
   * @private
   */
  prepareData(annotation, { includeId, isNewDraft } = {}) {
    const userGenerate =
      !annotation.userGenerate || annotation.sentUserGenerate;
    const currentDraft = this.findActiveDraft(annotation);
    const sessionTime = (Date.now() - annotation.loadedDate.getTime()) / 1000;
    const submittedTime = isNewDraft ? 0 : Number(annotation.leadTime ?? 0);
    const draftTime = Number(currentDraft?.lead_time ?? 0);
    const leadTime = submittedTime + draftTime + sessionTime;
    const startedAt = this.calculateStartedAt(
      currentDraft,
      annotation.loadedDate
    );

    const result = {
      lead_time: leadTime,
      result:
        (isNewDraft
          ? annotation.versions.draft
          : annotation.serializeAnnotation()) ?? [],
      draft_id: annotation.draftId,
      parent_prediction: annotation.parent_prediction,
      parent_annotation: annotation.parent_annotation,
      started_at: startedAt.toISOString(),
    };

    if (includeId && userGenerate) {
      result.id = Number.parseInt(annotation.pk);
    }

    return result;
  }

  /** @private */
  setLoading(isLoading, shouldReset = false) {
    // Avoid calling into Synapse which may invoke store mutations when the store is dead
    if (
      !this.datamanager ||
      !this.datamanager.store ||
      !isAlive(this.datamanager.store)
    ) {
      console.warn(
        "[SFWrapper] datamanager.store not alive; skipping setLoading"
      );
      return;
    }

    if (!this.sf) return;

    if (isFF(FF_LSDV_4620_3_ML) && shouldReset) this.sf.clearApp();
    try {
      this.sf.setFlags({ isLoading });
    } catch (err) {
      console.warn(
        "[SFWrapper] sf.setFlags failed or caused store mutation on dead tree:",
        err
      );
    }
    if (isFF(FF_LSDV_4620_3_ML) && shouldReset) this.sf.renderApp();
  }

  async withinLoadingState(callback) {
    let result;

    this.setLoading(true);
    if (callback) {
      result = await callback.call(this);
    }
    this.setLoading(false);

    return result;
  }

  destroy() {
    this.sfInstance?.destroy?.();
    this.sfInstance = null;
  }

  // Resolve live task node from the store on every access (don't cache MST nodes)
  get task() {
    return this.getTaskNode();
  }

  // Provide a defensive setter so external code that assigns `this.task = ...`
  // won't throw. We store the primitive `taskId` and resolve the node on access.
  set task(value) {
    try {
      this.taskId = value?.id ?? null;
    } catch (e) {
      // Defensive: ignore invalid assignments
    }
  }

  get taskID() {
    return this.task?.id ?? this.taskId;
  }

  get taskHistory() {
    return this.sf.taskHistory;
  }

  get currentAnnotation() {
    try {
      return this.sf.annotationStore.selected;
    } catch {
      return null;
    }
  }

  get annotations() {
    return this.sf.annotationStore.annotations;
  }

  get predictions() {
    return this.sf.annotationStore.predictions;
  }

  /** @returns {string|null} */
  get sfConfig() {
    return this.datamanager.store.labelingConfig;
  }

  /** @returns {Dict} */
  get project() {
    return this.datamanager.store.project;
  }

  /** @returns {string|null} */
  get instruction() {
    return (
      (
        this.project.instruction ??
        this.project.expert_instruction ??
        ""
      ).trim() || null
    );
  }

  get canPreloadTask() {
    return Boolean(this.preload?.interaction);
  }
}
