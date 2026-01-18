import { IconClose } from "@synapse/icons";
import { Button } from "../button/button";
import { useModalControls } from "./ModalPopup";

export const ModalCloseButton = () => {
  const modal = useModalControls();
  return (
    <button
      onClick={() => modal?.hide()}
      aria-label="Close modal"
      style={{
        background: 'transparent',
        border: 'none',
        cursor: 'pointer',
        padding: '8px',
        borderRadius: '8px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#6b7280',
        transition: 'all 0.2s ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
        e.currentTarget.style.color = '#c4b5fd';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = 'transparent';
        e.currentTarget.style.color = '#6b7280';
      }}
    >
      <IconClose style={{ width: '20px', height: '20px' }} />
    </button>
  );
};

