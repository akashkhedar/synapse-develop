import React, { Component } from "react";
import { observer, inject } from "mobx-react";
import { 
  RenderingEngine, 
  Enums, 
  init as initCornerstoneCore,
  imageLoader,
  cache,
} from "@cornerstonejs/core";
import {
  init as initCornerstoneTools,
  addTool,
  ToolGroupManager,
  WindowLevelTool,
  PanTool,
  ZoomTool,
  StackScrollTool,
  Enums as ToolsEnums
} from "@cornerstonejs/tools";
import { init as dicomImageLoaderInit } from "@cornerstonejs/dicom-image-loader";
import "./Dicom.scss";
import { isAlive } from "mobx-state-tree";

// Global Initialization Flag
let isCornerstoneInitialized = false;

async function initCornerstone() {
  if (isCornerstoneInitialized) return;
  
  try {
    await initCornerstoneCore();
    cache.setMaxCacheSize(256 * 1024 * 1024); // 256MB
    
    await initCornerstoneTools();
    await dicomImageLoaderInit({ maxWebWorkers: 2 });
    
    // Register Tools
    [WindowLevelTool, PanTool, ZoomTool, StackScrollTool].forEach(Tool => {
      try { addTool(Tool); } catch(e){}
    });

    isCornerstoneInitialized = true;
    console.log("[Dicom] Cornerstone initialized");

  } catch (error) {
    console.error("[Dicom] Failed to initialize:", error);
    throw error;
  }
}

class DicomView extends Component {
  constructor(props) {
    super(props);
    
    this.viewportRef = React.createRef();
    this.unmounted = false;
    
    const instanceId = Math.random().toString(36).substr(2, 6);
    this.renderingEngineId = `dicom-engine-${instanceId}`;
    this.viewportId = `dicom-viewport-${instanceId}`;
    this.toolGroupId = `dicom-tools-${instanceId}`;
    
    this.state = {
      isLoading: true,
      error: null,
      status: 'Loading...'
    };
    
    this.renderingEngine = null;
  }

  async componentDidMount() {
    this.unmounted = false;
    
    try {
      await initCornerstone();
      if (this.unmounted) return;
      await this.setupViewer();
    } catch (err) {
      console.error("[Dicom] Mount error:", err);
      if (!this.unmounted) {
        this.setState({ error: err.message, isLoading: false });
      }
    }
  }

  componentWillUnmount() {
    this.unmounted = true;
    this.cleanup();
  }
  
  cleanup() {
    try {
      ToolGroupManager.destroyToolGroup(this.toolGroupId);
    } catch (e) {}
    
    if (this.renderingEngine) {
      try { this.renderingEngine.destroy(); } catch (e) {}
      this.renderingEngine = null;
    }
  }

  async setupViewer() {
    if (this.unmounted) return;
    
    const element = this.viewportRef.current;
    if (!element) {
      setTimeout(() => this.setupViewer(), 100);
      return;
    }

    const { item } = this.props;
    if (!isAlive(item)) return;

    const imageUrl = item.parsedValue;
    
    if (!imageUrl) {
      throw new Error("No image URL provided");
    }

    // Clean up existing
    this.cleanup();

    // Create rendering engine
    this.renderingEngine = new RenderingEngine(this.renderingEngineId);

    // Enable viewport as STACK (2D)
    this.renderingEngine.enableElement({
      viewportId: this.viewportId,
      type: Enums.ViewportType.STACK,
      element,
      defaultOptions: {
        background: [0, 0, 0]
      }
    });

    // Setup tools
    this.setupTools();

    const viewport = this.renderingEngine.getViewport(this.viewportId);
    
    // Build imageId - handle different URL formats
    let imageId;
    if (imageUrl.startsWith('wadouri:') || imageUrl.startsWith('dicomweb:')) {
      imageId = imageUrl;
    } else if (imageUrl.endsWith('.dcm') || imageUrl.includes('/dicom')) {
      imageId = `wadouri:${imageUrl}`;
    } else {
      // Assume it's a regular image URL, use web image loader
      imageId = imageUrl;
    }

    console.log(`[Dicom] Loading image: ${imageId}`);
    
    try {
      // Set the stack with single image
      await viewport.setStack([imageId], 0);
      viewport.render();
      
      this.setState({ isLoading: false, status: 'Ready' });
      console.log("[Dicom] Image loaded successfully");
    } catch (loadError) {
      console.error("[Dicom] Failed to load image:", loadError);
      throw new Error(`Failed to load DICOM image: ${loadError.message}`);
    }
  }

  setupTools() {
    try {
      ToolGroupManager.destroyToolGroup(this.toolGroupId);
    } catch (e) {}
    
    const toolGroup = ToolGroupManager.createToolGroup(this.toolGroupId);
    
    toolGroup.addTool(WindowLevelTool.toolName);
    toolGroup.addTool(PanTool.toolName);
    toolGroup.addTool(ZoomTool.toolName);
    toolGroup.addTool(StackScrollTool.toolName);

    toolGroup.setToolActive(WindowLevelTool.toolName, {
      bindings: [{ mouseButton: ToolsEnums.MouseBindings.Primary }]
    });
    toolGroup.setToolActive(PanTool.toolName, {
      bindings: [{ mouseButton: ToolsEnums.MouseBindings.Auxiliary }]
    });
    toolGroup.setToolActive(ZoomTool.toolName, {
      bindings: [{ mouseButton: ToolsEnums.MouseBindings.Secondary }]
    });
    
    toolGroup.addViewport(this.viewportId, this.renderingEngineId);
  }

  render() {
    const { isLoading, error, status } = this.state;
    
    return (
      <div className="dicom-wrapper" style={{
        width: '100%', 
        height: '500px', 
        background: '#000', 
        color: 'white', 
        position: 'relative'
      }}>
        {error && (
          <div style={{
            padding: 20, 
            color: '#ff6b6b', 
            position: 'absolute', 
            top: 0, 
            left: 0,
            right: 0,
            background: 'rgba(0,0,0,0.9)',
            textAlign: 'center',
            zIndex: 10
          }}>
            Error: {error}
          </div>
        )}
        
        {isLoading && !error && (
          <div style={{
            padding: 20, 
            position: 'absolute', 
            top: 0, 
            left: 0,
            right: 0,
            background: 'rgba(0,0,0,0.8)',
            textAlign: 'center',
            zIndex: 10
          }}>
            {status}
          </div>
        )}
        
        <div 
          ref={this.viewportRef} 
          style={{
            width: '100%',
            height: '100%',
            position: 'relative'
          }}
          onContextMenu={e => e.preventDefault()}
        />
      </div>
    );
  }
}

const HtxDicomView = inject("store")(observer(DicomView));
export { HtxDicomView };
