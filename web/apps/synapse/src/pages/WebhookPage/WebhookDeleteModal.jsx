import { Button } from "@synapse/ui";
import { modal } from "../../components/Modal/Modal";
import { useModalControls } from "../../components/Modal/ModalPopup";
import { Space } from "../../components/Space/Space";
import { cn } from "../../utils/bem";

// Button Styles
const dangerButtonStyle = {
  minWidth: "90px",
  height: "36px",
  background: "rgba(239, 68, 68, 0.1)",
  border: "1px solid rgba(239, 68, 68, 0.3)",
  borderRadius: "0",
  color: "#fca5a5",
  fontSize: "13px",
  fontWeight: "600",
  textTransform: "uppercase",
  letterSpacing: "0.05em",
  cursor: "pointer",
  transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
  fontFamily: "'Space Grotesk', system-ui, sans-serif",
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  padding: "0 16px",
};

const neutralButtonStyle = {
  ...dangerButtonStyle,
  background: "transparent",
  border: "1px solid rgba(75, 85, 99, 0.5)",
  color: "#9ca3af",
};

const handleMouseEnter = (e, variant) => {
  if (variant === "danger") {
    e.currentTarget.style.background = "rgba(239, 68, 68, 0.18)";
    e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.5)";
    e.currentTarget.style.color = "#f87171";
    e.currentTarget.style.boxShadow = "0 4px 16px rgba(239, 68, 68, 0.2)";
  } else if (variant === "neutral") {
     e.currentTarget.style.borderColor = "rgba(139, 92, 246, 0.5)";
     e.currentTarget.style.color = "#c4b5fd";
  }
};

const handleMouseLeave = (e, variant) => {
  if (variant === "danger") {
    e.currentTarget.style.background = "rgba(239, 68, 68, 0.1)";
    e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.3)";
    e.currentTarget.style.color = "#fca5a5";
    e.currentTarget.style.boxShadow = "none";
  } else if (variant === "neutral") {
    e.currentTarget.style.background = "transparent";
    e.currentTarget.style.borderColor = "rgba(75, 85, 99, 0.5)";
    e.currentTarget.style.color = "#9ca3af";
  }
};

export const WebhookDeleteModal = ({ onDelete }) => {
  return modal({
    title: "Delete Webhook",
    body: () => {
      const rootClass = cn("webhook-delete-modal");
      return (
        <div className={rootClass} style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
          <div className={rootClass.elem("modal-text")} style={{ fontSize: '14px', color: '#d1d5db' }}>
            Are you sure you want to delete this webhook? This action cannot be undone.
          </div>
        </div>
      );
    },
    footer: () => {
      const ctrl = useModalControls();
      return (
        <Space align="end">
          <button
            style={neutralButtonStyle}
            onMouseEnter={(e) => handleMouseEnter(e, "neutral")}
            onMouseLeave={(e) => handleMouseLeave(e, "neutral")}
            onClick={() => {
              ctrl.hide();
            }}
          >
            Cancel
          </button>
          <button
            style={dangerButtonStyle}
            onMouseEnter={(e) => handleMouseEnter(e, "danger")}
            onMouseLeave={(e) => handleMouseLeave(e, "danger")}
            onClick={async () => {
              await onDelete();
              ctrl.hide();
            }}
          >
            Delete Webhook
          </button>
        </Space>
      );
    },
    style: { width: 512, borderRadius: 0, border: '1px solid #374151', background: '#000000' },
  });
};

