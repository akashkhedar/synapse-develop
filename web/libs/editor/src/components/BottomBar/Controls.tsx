/**
 * This panel is used with FF_1170 + FF_3873 in new interface,
 * but it's also used in old interface with FF_3873, but without FF_1170.
 * Only this component should get interface updates, other versions should be removed.
 */

import { observer } from "mobx-react";
import type React from "react";
import { useCallback, useState } from "react";

import { Button, ButtonGroup, type ButtonProps } from "@synapse/ui";
import { IconBan, IconChevronDown } from "@synapse/icons";
import { Dropdown } from "@synapse/ui";
import { Modal, useModalControls } from "../../common/Modal/Modal";
import { TextArea } from "../../common/TextArea/TextArea";
import type { CustomButtonType } from "../../stores/CustomButton";
import { cn } from "../../utils/bem";
import { FF_REVIEWER_FLOW, isFF } from "../../utils/feature-flags";
import { isDefined, toArray } from "../../utils/utilities";
import {
  AcceptButton,
  ButtonTooltip,
  controlsInjector,
  RejectButtonDefinition,
  SkipButton,
  UnskipButton,
} from "./buttons";

import "./Controls.scss";

// these buttons can be reused inside custom buttons or can be replaces with custom buttons
type SupportedInternalButtons = "accept" | "reject";
// special places for custom buttons — before, after or instead of internal buttons
type SpecialPlaces = "_before" | "_after" | "_replace";
// @todo should be Instance<typeof AppStore>["customButtons"] but it doesn't fit to itself
type CustomButtonsField = Map<
  SpecialPlaces | SupportedInternalButtons,
  | CustomButtonType
  | SupportedInternalButtons
  | Array<CustomButtonType | SupportedInternalButtons>
>;
type ControlButtonProps = {
  button: CustomButtonType;
  disabled: boolean;
  variant?: ButtonProps["variant"];
  look?: ButtonProps["look"];
  onClick: (e: React.MouseEvent) => void;
};

export const EMPTY_SUBMIT_TOOLTIP = "Empty annotations denied in this project";

/**
 * Custom action button component, rendering buttons from store.customButtons
 */
const ControlButton = observer(
  ({ button, disabled, onClick, variant, look }: ControlButtonProps) => {
    return (
      <Button
        {...button.props}
        variant={button.variant ?? variant}
        look={button.look ?? look}
        tooltip={button.tooltip}
        className="w-[150px]"
        aria-label={button.ariaLabel}
        disabled={button.disabled || disabled}
        onClick={onClick}
      >
        {button.title}
      </Button>
    );
  }
);

/**
 * Rejection modal component for expert review
 */
const RejectModal = observer(
  ({
    disabled,
    isInProgress,
    setIsInProgress,
    annotation,
    store,
  }: {
    disabled: boolean;
    isInProgress: boolean;
    setIsInProgress: (value: boolean) => void;
    annotation: any;
    store: any;
  }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [rejectionReason, setRejectionReason] = useState("");
    const [additionalNotes, setAdditionalNotes] = useState("");
    const [submitting, setSubmitting] = useState(false);

    const rejectionReasons = [
      { value: "disagreement", label: "High Annotator Disagreement" },
      { value: "low_quality", label: "Low Quality Annotations" },
      { value: "incorrect_labels", label: "Incorrect Labels" },
      { value: "incomplete", label: "Incomplete Annotation" },
      { value: "ambiguous", label: "Ambiguous Data" },
      { value: "other", label: "Other (Please specify)" },
    ];

    const handleReject = async () => {
      if (!rejectionReason) {
        alert("Please select a rejection reason");
        return;
      }

      setSubmitting(true);
      setIsInProgress(true);

      try {
        const taskId = store.task?.id;
        if (!taskId) {
          alert("Task ID not found");
          setSubmitting(false);
          setIsInProgress(false);
          return;
        }
        const response = await fetch(
          `/api/annotators/expert/review/${taskId}/action`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({
              action: "reject",
              rejection_reason: rejectionReason,
              review_notes:
                additionalNotes ||
                store.commentStore.currentComment[annotation.id]?.text ||
                "",
              require_reannotation: true,
            }),
          }
        );

        if (response.ok) {
          const result = await response.json();
          console.log(
            `❌ Annotation rejected. ${
              result.annotators_notified || 0
            } annotators notified.`
          );
          setIsOpen(false);
          // Move to next task without reloading
          if (store.hasInterface("topbar:prevnext")) {
            setTimeout(() => store.skipTask({}), 300);
          }
        } else {
          const data = await response.json();
          console.error("Failed to reject:", data.error || "Unknown error");
          alert(data.error || "Failed to reject annotation");
        }
      } catch (error) {
        console.error("Expert reject error:", error);
        alert("Failed to reject annotation");
      } finally {
        setSubmitting(false);
        setIsInProgress(false);
      }
    };

    return (
      <>
        <Button
          variant="negative"
          className="w-[150px] btn_danger"
          disabled={disabled || isInProgress}
          onClick={() => {
            setRejectionReason("");
            setAdditionalNotes("");
            setIsOpen(true);
          }}
        >
          Reject
        </Button>

        <Modal
          visible={isOpen}
          onHide={() => !submitting && setIsOpen(false)}
          title="Reject Annotation"
          style={{ width: 500 }}
          footer={
            <div
              style={{
                display: "flex",
                gap: "8px",
                justifyContent: "flex-end",
              }}
            >
              <Button
                look="outlined"
                disabled={submitting}
                onClick={() => setIsOpen(false)}
              >
                Cancel
              </Button>
              <Button
                variant="negative"
                disabled={!rejectionReason || submitting}
                onClick={handleReject}
              >
                {submitting ? "Rejecting..." : "Reject & Notify"}
              </Button>
            </div>
          }
        >
          <div
            style={{ display: "flex", flexDirection: "column", gap: "16px" }}
          >
            <div>
              <label
                style={{
                  display: "block",
                  marginBottom: "12px",
                  fontWeight: 500,
                  fontSize: "14px",
                }}
              >
                Select Reason for Rejection:
              </label>
              <div
                style={{ display: "flex", flexDirection: "column", gap: "8px" }}
              >
                {rejectionReasons.map((reason) => (
                  <div
                    key={reason.value}
                    onClick={() => setRejectionReason(reason.value)}
                    style={{
                      padding: "12px 16px",
                      border:
                        rejectionReason === reason.value
                          ? "2px solid #1890ff"
                          : "1px solid #d9d9d9",
                      borderRadius: "6px",
                      cursor: "pointer",
                      backgroundColor:
                        rejectionReason === reason.value ? "#e6f7ff" : "#fff",
                      transition: "all 0.2s",
                      fontWeight: rejectionReason === reason.value ? 500 : 400,
                    }}
                    onMouseEnter={(e) => {
                      if (rejectionReason !== reason.value) {
                        e.currentTarget.style.borderColor = "#40a9ff";
                        e.currentTarget.style.backgroundColor = "#f5f5f5";
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (rejectionReason !== reason.value) {
                        e.currentTarget.style.borderColor = "#d9d9d9";
                        e.currentTarget.style.backgroundColor = "#fff";
                      }
                    }}
                  >
                    {reason.label}
                  </div>
                ))}
              </div>
            </div>

            {rejectionReason && (
              <div>
                <label
                  style={{
                    display: "block",
                    marginBottom: "8px",
                    fontWeight: 500,
                  }}
                >
                  Additional Notes{" "}
                  {rejectionReason === "other" ? "(Required)" : "(Optional)"}
                </label>
                <TextArea
                  value={additionalNotes || ""}
                  onChange={(value) => setAdditionalNotes(value)}
                  placeholder={
                    rejectionReason === "other"
                      ? "Please describe the issue..."
                      : "Add any additional context or feedback for the annotators..."
                  }
                  rows={4}
                />
              </div>
            )}

            <div
              style={{
                padding: "12px",
                backgroundColor: "#fff3cd",
                borderRadius: "4px",
                fontSize: "13px",
                color: "#856404",
              }}
            >
              <strong>Note:</strong> All annotators will be notified and the
              task will be reassigned for reannotation.
            </div>
          </div>
        </Modal>
      </>
    );
  }
);

export const Controls = controlsInjector(
  observer(
    ({
      store,
      history,
      annotation,
    }: {
      store: any;
      history: any;
      annotation: any;
    }) => {
      const isReview = store.hasInterface("review") || annotation.canBeReviewed;
      const isNotQuickView = store.hasInterface("topbar:prevnext");
      const historySelected = isDefined(store.annotationStore.selectedHistory);
      const {
        userGenerate,
        sentUserGenerate,
        versions,
        results,
        editable: annotationEditable,
      } = annotation;
      const dropdownTrigger = cn("dropdown").elem("trigger").toClassName();
      const customButtons: CustomButtonsField = store.customButtons;
      const buttons: React.ReactNode[] = [];

      const [isInProgress, setIsInProgress] = useState(false);
      const disabled =
        !annotationEditable ||
        store.isSubmitting ||
        historySelected ||
        isInProgress;
      const submitDisabled =
        store.hasInterface("annotations:deny-empty") && results.length === 0;

      /** Check all things related to comments and then call the action if all is good */
      const handleActionWithComments = useCallback(
        async (
          e: React.MouseEvent,
          callback: () => any,
          errorMessage: string
        ) => {
          const { addedCommentThisSession, currentComment, commentFormSubmit } =
            store.commentStore;
          const comment = currentComment[annotation.id];
          // accept both old and new comment formats
          const commentText = (comment?.text ?? comment)?.trim();

          if (isInProgress) return;
          setIsInProgress(true);

          const selected = store.annotationStore?.selected;

          if (addedCommentThisSession) {
            selected?.submissionInProgress();
            callback();
          } else if (commentText) {
            e.preventDefault();
            selected?.submissionInProgress();
            await commentFormSubmit();
            callback();
          } else {
            store.commentStore.setTooltipMessage(errorMessage);
          }
          setIsInProgress(false);
        },
        [
          store.rejectAnnotation,
          store.skipTask,
          store.commentStore.currentComment,
          store.commentStore.commentFormSubmit,
          store.commentStore.addedCommentThisSession,
          isInProgress,
        ]
      );

      if (annotation.isNonEditableDraft) return <></>;

      const buttonsBefore = customButtons.get("_before");
      const buttonsReplacement = customButtons.get("_replace");
      const firstToRender = buttonsReplacement ?? buttonsBefore;

      // either we render _before buttons and then the rest, or we render only _replace buttons
      if (firstToRender) {
        const allButtons = toArray(firstToRender);
        for (const customButton of allButtons) {
          // @todo make a list of all internal buttons and use them here to mix custom buttons with internal ones
          // string buttons is a way to render internal buttons
          if (typeof customButton === "string") {
            if (customButton === "accept") {
              // just an example of internal button usage
              // @todo move buttons to separate components
              buttons.push(
                <AcceptButton
                  key={customButton}
                  disabled={disabled}
                  history={history}
                  store={store}
                />
              );
            }
          } else {
            buttons.push(
              <ControlButton
                key={customButton.name}
                disabled={disabled}
                button={customButton}
                onClick={() => store.handleCustomButton?.(customButton)}
              />
            );
          }
        }
      }

      if (buttonsReplacement) {
        return <div className={cn("controls").toClassName()}>{buttons}</div>;
      }

      // Check if user is an expert reviewing a task
      const isExpertReview = store.hasInterface("expert-review");

      // Check User Role
      const userRole = (window as any).APP_SETTINGS?.user?.role;
      // Define roles
      const MANAGER_ROLES = ["OW", "AD", "MA"];
      const ANNOTATOR_ROLES = ["AN", "RE"]; // RE might be reviewer, but often acts as annotator in some flows
      const isClient = !MANAGER_ROLES.includes(userRole) && !ANNOTATOR_ROLES.includes(userRole) && !isExpertReview && !isReview;

      if (isClient) {
        // Client View: Show Close Button
         buttons.push(
          <ButtonTooltip key="close" title="Close task view">
            <Button
              aria-label="Close task"
              className="w-[150px] btn_outline"
              look="outlined"
              onClick={() => {
                 if (history.length > 1) {
                    window.history.back();
                 } else {
                    // Fallback if no history (e.g. direct link), maybe close window or redirect
                    // Trying to close the stream/modal logic
                    const searchParams = new URLSearchParams(window.location.search);
                    searchParams.set("exitStream", "true");
                    const newRelativePathQuery = `${window.location.pathname}?${searchParams.toString()}`;
                    window.location.href = newRelativePathQuery; 
                 }
              }}
            >
              Close
            </Button>
          </ButtonTooltip>
        );
        return <div className={cn("controls").toClassName()}>{buttons}</div>;
      }


      if (isExpertReview) {
        // Expert Accept Button
        buttons.push(
          <Button
            key="expert-accept"
            variant="primary"
            className="w-[150px] btn_success"
            disabled={disabled}
            onClick={async () => {
              if (disabled || isInProgress) return;
              setIsInProgress(true);
              try {
                const taskId = store.task?.id;
                if (!taskId) {
                  alert("Task ID not found");
                  setIsInProgress(false);
                  return;
                }
                const response = await fetch(
                  `/api/annotators/expert/review/${taskId}/action`,
                  {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    credentials: "include",
                    body: JSON.stringify({
                      action: "accept",
                      review_notes:
                        store.commentStore.currentComment[annotation.id]
                          ?.text || "",
                    }),
                  }
                );

                if (response.ok) {
                  console.log("✅ Annotation accepted and finalized!");
                  // Move to next task without reloading
                  if (store.hasInterface("topbar:prevnext")) {
                    setTimeout(() => store.skipTask({}), 300);
                  }
                } else {
                  const data = await response.json();
                  console.error(
                    "Failed to accept:",
                    data.error || "Unknown error"
                  );
                  alert(data.error || "Failed to accept annotation");
                }
              } catch (error) {
                console.error("Expert accept error:", error);
                alert("Failed to accept annotation");
              } finally {
                setIsInProgress(false);
              }
            }}
          >
            Accept
          </Button>
        );

        // Expert Reject Button with Modal
        buttons.push(
          <RejectModal
            key="expert-reject"
            disabled={disabled}
            isInProgress={isInProgress}
            setIsInProgress={setIsInProgress}
            annotation={annotation}
            store={store}
          />
        );

        return <div className={cn("controls").toClassName()}>{buttons}</div>;
      }

      if (isReview) {
        const customRejectButtons = toArray(customButtons.get("reject"));
        const hasCustomReject = customRejectButtons.length > 0;
        const originalRejectButton = RejectButtonDefinition;

        // @todo implement reuse of internal buttons later (they are set as strings)
        const rejectButtons: any[] = hasCustomReject
          ? customRejectButtons.filter((button) => typeof button !== "string")
          : [originalRejectButton];

        rejectButtons.forEach((button) => {
          const action = hasCustomReject
            ? () => store.handleCustomButton?.(button)
            : () => store.rejectAnnotation({});

          const onReject = async (e: React.MouseEvent) => {
            const selected = store.annotationStore?.selected;

            if (store.hasInterface("comments:reject")) {
              handleActionWithComments(
                e,
                action,
                "Please enter a comment before rejecting"
              );
            } else {
              selected?.submissionInProgress();
              await store.commentStore.commentFormSubmit();
              action();
            }
          };

          buttons.push(
            <ControlButton
              key={button.name}
              button={button}
              disabled={disabled}
              onClick={onReject}
            />
          );
        });
        buttons.push(
          <AcceptButton
            key="review-accept"
            disabled={disabled}
            history={history}
            store={store}
          />
        );
      } else if (annotation.skipped) {
        buttons.push(
          <div
            className={cn("controls").elem("skipped-info").toClassName()}
            key="skipped"
          >
            <IconBan /> Was skipped
          </div>
        );
        buttons.push(
          <UnskipButton key="unskip" disabled={disabled} store={store} />
        );
      } else {
        if (store.hasInterface("skip")) {
          const onSkipWithComment = (
            e: React.MouseEvent,
            action: () => any
          ) => {
            handleActionWithComments(
              e,
              action,
              "Please enter a comment before skipping"
            );
          };

          buttons.push(
            <SkipButton
              key="skip"
              disabled={disabled}
              store={store}
              onSkipWithComment={onSkipWithComment}
            />
          );
        }

        const isDisabled = disabled || submitDisabled;

        const useExitOption = !isDisabled && isNotQuickView;

        const SubmitOption = ({
          isUpdate,
          onClickMethod,
        }: {
          isUpdate: boolean;
          onClickMethod: () => any;
        }) => {
          return (
            <div className="p-tighter rounded">
              <Button
                name="submit-option"
                look="string"
                size="small"
                className="w-[150px]"
                onClick={async (event) => {
                  event.preventDefault();

                  const selected = store.annotationStore?.selected;

                  selected?.submissionInProgress();

                  if ("URLSearchParams" in window) {
                    const searchParams = new URLSearchParams(
                      window.location.search
                    );

                    searchParams.set("exitStream", "true");
                    const newRelativePathQuery = `${
                      window.location.pathname
                    }?${searchParams.toString()}`;

                    window.history.pushState(null, "", newRelativePathQuery);
                  }

                  await store.commentStore.commentFormSubmit();
                  onClickMethod();
                }}
              >
                {`${isUpdate ? "Update" : "Submit"} and exit`}
              </Button>
            </div>
          );
        };

        if (
          userGenerate ||
          (store.explore && !userGenerate && store.hasInterface("submit"))
        ) {
          const title = submitDisabled
            ? EMPTY_SUBMIT_TOOLTIP
            : "Save results: [ Ctrl+Enter ]";

          buttons.push(
            <ButtonTooltip key="submit" title={title}>
              <div
                className={cn("controls").elem("tooltip-wrapper").toClassName()}
              >
                <ButtonGroup>
                  <Button
                    aria-label="Submit current annotation"
                    name="submit"
                    className="w-[150px] btn_primary"
                    disabled={isDisabled}
                    onClick={async (event) => {
                      if (
                        (event.target as HTMLButtonElement).classList.contains(
                          dropdownTrigger
                        )
                      )
                        return;
                      const selected = store.annotationStore?.selected;

                      selected?.submissionInProgress();
                      await store.commentStore.commentFormSubmit();
                      store.submitAnnotation();
                    }}
                  >
                    Submit
                  </Button>
                  {useExitOption ? (
                    <Dropdown.Trigger
                      alignment="top-right"
                      content={
                        <div className="p-tight bg-neutral-surface">
                          <SubmitOption
                            onClickMethod={store.submitAnnotation}
                            isUpdate={false}
                          />
                        </div>
                      }
                    >
                      <Button
                        disabled={isDisabled}
                        aria-label="Submit annotation"
                      >
                        <IconChevronDown />
                      </Button>
                    </Dropdown.Trigger>
                  ) : null}
                </ButtonGroup>
              </div>
            </ButtonTooltip>
          );
        } else if (
          (userGenerate && sentUserGenerate) ||
          (!userGenerate && store.hasInterface("update"))
        ) {
          const isUpdate = Boolean(
            isFF(FF_REVIEWER_FLOW) || sentUserGenerate || versions.result
          );
          // no changes were made over previously submitted version — no drafts, no pending changes
          const noChanges =
            isFF(FF_REVIEWER_FLOW) && !history.canUndo && !annotation.draftId;
          const isUpdateDisabled = isDisabled || noChanges;
          const button = (
            <ButtonTooltip
              key="update"
              title={
                noChanges
                  ? "No changes were made"
                  : "Update this task: [ Ctrl+Enter ]"
              }
            >
              <ButtonGroup>
                <Button
                  aria-label="submit"
                  name="submit"
                  className={`w-[150px] ${isUpdate ? "btn_outline" : "btn_primary"}`}
                  disabled={isUpdateDisabled}
                  onClick={async (event) => {
                    if (
                      (event.target as HTMLButtonElement).classList.contains(
                        dropdownTrigger
                      )
                    )
                      return;
                    const selected = store.annotationStore?.selected;

                    selected?.submissionInProgress();
                    await store.commentStore.commentFormSubmit();
                    store.updateAnnotation();
                  }}
                >
                  {isUpdate ? "Update" : "Submit"}
                </Button>
                {useExitOption ? (
                  <Dropdown.Trigger
                    alignment="top-right"
                    content={
                      <SubmitOption
                        onClickMethod={store.updateAnnotation}
                        isUpdate={isUpdate}
                      />
                    }
                  >
                    <Button
                      disabled={isUpdateDisabled}
                      aria-label="Update annotation"
                    >
                      <IconChevronDown />
                    </Button>
                  </Dropdown.Trigger>
                ) : null}
              </ButtonGroup>
            </ButtonTooltip>
          );

          buttons.push(button);
        }
      }

      return <div className={cn("controls").toClassName()}>{buttons}</div>;
    }
  )
);

