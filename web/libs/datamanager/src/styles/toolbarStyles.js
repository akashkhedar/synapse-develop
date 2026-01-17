// Shared toolbar button styles - use this in all toolbar button components
// Import: import { toolbarButtonStyle, toolbarButtonActiveStyle } from '../../../styles/toolbarStyles';

export const toolbarButtonStyle = {
  background: 'black',
  border: '1px solid rgba(55, 65, 81, 0.5)',
  borderRadius: '10px',
  color: '#c4b5fd',
  fontWeight: 600,
  fontSize: '13px',
  height: '32px',
  padding: '0 14px',
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: '6px',
};

export const toolbarButtonActiveStyle = {
  ...toolbarButtonStyle,
  background: 'rgba(139, 92, 246, 0.2)',
};

export const toolbarToggleContainerStyle = {
  background: 'black',
  border: '1px solid rgba(55, 65, 81, 0.5)',
  borderRadius: '10px',
  height: '32px',
  display: 'flex',
  alignItems: 'center',
  gap: '2px',
  padding: '3px',
};

export const toolbarToggleButtonStyle = {
  background: 'transparent',
  border: 'none',
  borderRadius: '7px',
  color: '#c4b5fd',
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  height: '26px',
  width: '26px',
  padding: '0',
};

export const toolbarToggleButtonActiveStyle = {
  ...toolbarToggleButtonStyle,
  background: 'rgba(139, 92, 246, 0.2)',
};
