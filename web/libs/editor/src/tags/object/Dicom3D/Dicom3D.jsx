import React from "react";
import { observer, inject } from "mobx-react";
import "./Dicom3D.scss";

/**
 * Dicom3D - 3D Volume Viewer (Disabled)
 * 
 * This component previously attempted 3D volume rendering with Cornerstone3D,
 * but has been disabled due to stability issues with WebGL context management.
 * 
 * For DICOM viewing, use the standard <Dicom> tag which provides 2D viewing.
 */
const Dicom3DView = observer(({ item }) => {
  return (
    <div className="dicom-3d-disabled" style={{
      width: '100%',
      height: '400px',
      background: '#1a1a1a',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexDirection: 'column',
      color: '#888',
      border: '1px solid #333',
      borderRadius: '4px'
    }}>
      <div style={{ fontSize: '48px', marginBottom: '16px' }}>🏥</div>
      <h3 style={{ margin: '0 0 8px 0', color: '#fff' }}>3D Volume Viewer</h3>
      <p style={{ margin: '0', textAlign: 'center', maxWidth: '400px' }}>
        3D volume rendering is currently disabled.<br/>
        Please use the standard <code>&lt;Dicom&gt;</code> tag for 2D DICOM viewing.
      </p>
    </div>
  );
});

const HtxDicom3DView = inject("store")(Dicom3DView);
export { HtxDicom3DView };
