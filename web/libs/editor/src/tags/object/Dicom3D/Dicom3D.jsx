import React, { Component } from "react";
import { observer, inject } from "mobx-react";
import { 
  RenderingEngine, 
  Enums, 
  volumeLoader, 
  init as initCornerstoneCore,
  cache,
  imageRetrievalPoolManager,
  imageLoadPoolManager,
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
import "./Dicom3D.scss";
import { isAlive } from "mobx-state-tree";

// Global Initialization Flag
let isCornerstoneInitialized = false;

// Maximum images to load - prevents GPU memory exhaustion
const MAX_IMAGES_FOR_VOLUME = 200;

async function initCornerstone() {
  if (isCornerstoneInitialized) return;
  
  // Check COOP/COEP
  if (window.crossOriginIsolated) {
      console.log("[Dicom3D] Cross-Origin Isolated: YES");
  } else {
      console.warn("[Dicom3D] Cross-Origin Isolated: NO");
  }

  try {
    // 1. Initialize Core
    await initCornerstoneCore();
    console.log("[Dicom3D] Core initialized");
    
    // 2. Configure Cache Size - REDUCED for integrated graphics
    // 256MB is safer for most GPUs
    cache.setMaxCacheSize(256 * 1024 * 1024);
    console.log("[Dicom3D] Cache size set to 256MB");
    
    // 3. Configure Request Pool Managers - VERY LOW for stability
    // Lower concurrent requests = less GPU pressure
    const poolLimits = { interaction: 2, thumbnail: 2, prefetch: 1 };
    
    try {
      if (imageRetrievalPoolManager?.setMaxSimultaneousRequests) {
        imageRetrievalPoolManager.setMaxSimultaneousRequests('interaction', poolLimits.interaction);
        imageRetrievalPoolManager.setMaxSimultaneousRequests('thumbnail', poolLimits.thumbnail);
        imageRetrievalPoolManager.setMaxSimultaneousRequests('prefetch', poolLimits.prefetch);
      }
      
      if (imageLoadPoolManager?.setMaxSimultaneousRequests) {
        imageLoadPoolManager.setMaxSimultaneousRequests('interaction', poolLimits.interaction);
        imageLoadPoolManager.setMaxSimultaneousRequests('thumbnail', poolLimits.thumbnail);
        imageLoadPoolManager.setMaxSimultaneousRequests('prefetch', poolLimits.prefetch);
      }
      console.log("[Dicom3D] Pool managers configured (low concurrency)");
    } catch (poolError) {
      console.warn("[Dicom3D] Could not configure pool managers:", poolError);
    }
    
    // 4. Initialize Tools
    await initCornerstoneTools();
    console.log("[Dicom3D] Tools initialized");
    
    // 5. Initialize DICOM Image Loader with minimal workers
    await dicomImageLoaderInit({ maxWebWorkers: 1 });
    console.log("[Dicom3D] DICOM Image Loader initialized"); 
    
    // 6. Register Tools
    [WindowLevelTool, PanTool, ZoomTool, StackScrollTool].forEach(Tool => {
        try { addTool(Tool); } catch(e){}
    });

    isCornerstoneInitialized = true;
    console.log("[Dicom3D] System Initialized Successfully");

  } catch (error) {
    console.error("[Dicom3D] Failed to initialize:", error);
    throw error;
  }
}

/**
 * MPR Viewport Configuration with explicit camera vectors
 */
const VIEWPORT_CONFIG = {
  AXIAL: {
    id: 'axial-viewport',
    orientation: Enums.OrientationAxis.AXIAL,
    label: 'AXIAL',
    viewUp: [0, -1, 0],
    viewPlaneNormal: [0, 0, -1]
  },
  SAGITTAL: {
    id: 'sagittal-viewport',
    orientation: Enums.OrientationAxis.SAGITTAL,
    label: 'SAGITTAL',
    viewUp: [0, 0, 1],
    viewPlaneNormal: [1, 0, 0]
  },
  CORONAL: {
    id: 'coronal-viewport',
    orientation: Enums.OrientationAxis.CORONAL,
    label: 'CORONAL',
    viewUp: [0, 0, 1],
    viewPlaneNormal: [0, 1, 0]
  }
};

class Dicom3DView extends Component {
  constructor(props) {
    super(props);
    
    this.viewportRefs = {
      AXIAL: React.createRef(),
      SAGITTAL: React.createRef(),
      CORONAL: React.createRef()
    };

    this.unmounted = false;
    this.contextLost = false;
    
    const instanceId = Math.random().toString(36).substr(2, 6);
    this.renderingEngineId = `mpr-engine-${instanceId}`;
    this.toolGroupId = `mpr-tools-${instanceId}`;
    
    this.state = {
      isLoading: true,
      error: null,
      status: 'Initializing...',
      imageCount: 0,
      loadedCount: 0
    };
    
    this.renderingEngine = null;
    this.volumeId = null;
    this.volume = null;
    
    // Bind context handlers
    this.handleContextLost = this.handleContextLost.bind(this);
    this.handleContextRestored = this.handleContextRestored.bind(this);
  }

  async componentDidMount() {
    this.unmounted = false;
    
    try {
      await initCornerstone();
      if (this.unmounted) return;
      await this.setupMPRViewer();
    } catch (err) {
      console.error("[Dicom3D] Mount error:", err);
      if (!this.unmounted) {
        this.setState({ error: err.message, isLoading: false });
      }
    }
  }

  componentWillUnmount() {
    this.unmounted = true;
    this.cleanup();
  }
  
  handleContextLost(event) {
    console.warn("[Dicom3D] WebGL context lost!");
    event.preventDefault();
    this.contextLost = true;
    
    // Cancel volume loading if in progress
    if (this.volume?.cancelLoading) {
      try { this.volume.cancelLoading(); } catch (e) {}
    }
    
    this.setState({
      error: 'GPU memory exhausted. Try refreshing the page or using a smaller dataset.',
      status: 'WebGL Context Lost'
    });
  }
  
  handleContextRestored() {
    console.log("[Dicom3D] WebGL context restored");
    this.contextLost = false;
    
    // Attempt recovery after delay
    setTimeout(() => {
      if (!this.unmounted && !this.contextLost) {
        this.setState({ error: null, status: 'Recovering...' });
        this.cleanup();
        this.setupMPRViewer();
      }
    }, 1000);
  }
  
  setupContextLossHandlers() {
    const viewportIds = ['AXIAL', 'SAGITTAL', 'CORONAL'];
    
    for (const vpId of viewportIds) {
      const viewport = this.renderingEngine?.getViewport(vpId);
      if (viewport) {
        const canvas = viewport.canvas;
        if (canvas) {
          canvas.addEventListener('webglcontextlost', this.handleContextLost, false);
          canvas.addEventListener('webglcontextrestored', this.handleContextRestored, false);
        }
      }
    }
    console.log("[Dicom3D] Context loss handlers attached");
  }
  
  removeContextLossHandlers() {
    const viewportIds = ['AXIAL', 'SAGITTAL', 'CORONAL'];
    
    for (const vpId of viewportIds) {
      try {
        const viewport = this.renderingEngine?.getViewport(vpId);
        if (viewport?.canvas) {
          viewport.canvas.removeEventListener('webglcontextlost', this.handleContextLost, false);
          viewport.canvas.removeEventListener('webglcontextrestored', this.handleContextRestored, false);
        }
      } catch (e) {}
    }
  }
  
  cleanup() {
    // Remove context handlers first
    this.removeContextLossHandlers();
    
    // Cancel volume loading
    if (this.volume?.cancelLoading) {
      try { this.volume.cancelLoading(); } catch (e) {}
    }
    
    // Destroy tool group
    try {
      ToolGroupManager.destroyToolGroup(this.toolGroupId);
    } catch (e) {}
    
    // Destroy rendering engine
    if (this.renderingEngine) {
      try { this.renderingEngine.destroy(); } catch (e) {}
      this.renderingEngine = null;
    }
    
    // Purge cache to free GPU memory
    try { cache.purgeCache(); } catch (e) {}
    
    this.volume = null;
    this.volumeId = null;
  }

  async loadImageIdsFromZip(zipUrl) {
    console.log(`[Dicom3D] Requesting processing for ZIP: ${zipUrl}`);
    this.setState({ status: 'Processing on server...' });

    const apiUrl = `/api/import/dicom-process/?url=${encodeURIComponent(zipUrl)}`;
    
    const response = await fetch(apiUrl);
    
    if (!response.ok) {
      const text = await response.text();
      let msg = text;
      try { msg = JSON.parse(text).error; } catch(e){}
      throw new Error(msg || `Server Error: ${response.status}`);
    }

    const data = await response.json();
    let serverImageIds = data.imageIds;
    
    if (!serverImageIds?.length) {
      throw new Error("No DICOM images returned from server");
    }

    console.log(`[Dicom3D] Server returned ${serverImageIds.length} images`);
    
    // CRITICAL: Limit images to prevent GPU exhaustion
    if (serverImageIds.length > MAX_IMAGES_FOR_VOLUME) {
      console.warn(`[Dicom3D] Limiting images from ${serverImageIds.length} to ${MAX_IMAGES_FOR_VOLUME} to prevent GPU exhaustion`);
      
      // Sample evenly across the dataset
      const step = serverImageIds.length / MAX_IMAGES_FOR_VOLUME;
      const sampledIds = [];
      for (let i = 0; i < MAX_IMAGES_FOR_VOLUME; i++) {
        const idx = Math.floor(i * step);
        sampledIds.push(serverImageIds[idx]);
      }
      serverImageIds = sampledIds;
      
      this.setState({ 
        status: `Using ${MAX_IMAGES_FOR_VOLUME} of ${data.imageIds.length} images (GPU limit)` 
      });
    }
    
    this.setState({ imageCount: serverImageIds.length });
    
    // Prefix with 'wadouri:' for Cornerstone DICOM Image Loader
    return serverImageIds.map(url => `wadouri:${url}`);
  }

  async setupMPRViewer() {
    if (this.unmounted || this.contextLost) return;
    
    // Wait for DOM elements
    const axialEl = this.viewportRefs.AXIAL.current;
    const sagittalEl = this.viewportRefs.SAGITTAL.current;
    const coronalEl = this.viewportRefs.CORONAL.current;
    
    if (!axialEl || !sagittalEl || !coronalEl) {
      console.warn("[Dicom3D] Viewports not ready. Retrying...");
      setTimeout(() => this.setupMPRViewer(), 100);
      return;
    }

    const { item } = this.props;
    if (!isAlive(item)) return;

    const zipUrl = item.parsedValue;
    
    if (!zipUrl?.endsWith('.zip')) {
      throw new Error("Please provide a ZIP file for 3D Demo");
    }

    // 1. Load Image IDs (with limiting)
    const imageIds = await this.loadImageIdsFromZip(zipUrl);
    if (this.unmounted || this.contextLost) return;

    // 2. Cleanup any existing resources
    this.cleanup();

    // 3. Create new rendering engine
    this.setState({ status: 'Creating viewports...' });
    this.renderingEngine = new RenderingEngine(this.renderingEngineId);

    // 4. Enable each viewport
    const viewportIds = ['AXIAL', 'SAGITTAL', 'CORONAL'];
    
    for (const vpId of viewportIds) {
      const config = VIEWPORT_CONFIG[vpId];
      const element = this.viewportRefs[vpId].current;
      
      console.log(`[Dicom3D] Enabling viewport: ${vpId}`);
      
      this.renderingEngine.enableElement({
        viewportId: vpId,
        type: Enums.ViewportType.ORTHOGRAPHIC,
        element,
        defaultOptions: {
          orientation: config.orientation,
          background: [0, 0, 0]
        }
      });
    }
    
    // Setup context loss handlers AFTER viewports are created
    this.setupContextLossHandlers();
    
    this.renderingEngine.resize(true);
    console.log("[Dicom3D] All viewports enabled");
    
    if (this.unmounted || this.contextLost) return;

    // 5. Create the volume
    const volumeName = `vol-${Math.random().toString(36).substr(2, 6)}`;
    this.volumeId = `cornerstoneStreamingImageVolume:${volumeName}`;
    
    this.setState({ status: `Creating volume with ${imageIds.length} images...` });
    console.log(`[Dicom3D] Creating volume: ${this.volumeId}`);
    
    this.volume = await volumeLoader.createAndCacheVolume(this.volumeId, { imageIds });
    
    if (this.unmounted || this.contextLost) return;

    // 6. Setup tools
    this.setupTools();

    // 7. Set volume on each viewport
    this.setState({ status: 'Binding volume to viewports...' });
    
    for (const vpId of viewportIds) {
      const viewport = this.renderingEngine.getViewport(vpId);
      if (viewport) {
        await viewport.setVolumes([{ volumeId: this.volumeId }]);
        console.log(`[Dicom3D] Volume bound to: ${vpId}`);
      }
    }
    
    if (this.unmounted || this.contextLost) return;

    // 8. Load the volume data
    this.setState({ status: 'Loading volume data (this may take a while)...' });
    console.log("[Dicom3D] Starting volume load...");
    
    await this.volume.load();
    
    console.log("[Dicom3D] Volume load completed");
    
    if (this.unmounted || this.contextLost) return;

    // 9. Set camera orientation and render
    console.log("[Dicom3D] Setting camera orientations...");
    
    for (const vpId of viewportIds) {
      const viewport = this.renderingEngine.getViewport(vpId);
      const config = VIEWPORT_CONFIG[vpId];
      
      if (viewport && config) {
        console.log(`[Dicom3D] Configuring camera for ${vpId}`);
        
        // Set explicit camera orientation
        viewport.setCamera({
          viewUp: config.viewUp,
          viewPlaneNormal: config.viewPlaneNormal
        });
        
        // Fit volume to viewport
        viewport.resetCamera();
        
        // Render
        viewport.render();
        
        console.log(`[Dicom3D] ${vpId} rendered`);
      }
    }
    
    this.renderingEngine.resize(true);
    
    console.log("[Dicom3D] MPR setup complete");
    this.setState({ isLoading: false, status: 'Ready' });
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
    toolGroup.setToolActive(StackScrollTool.toolName);

    ['AXIAL', 'SAGITTAL', 'CORONAL'].forEach(vpId => {
      toolGroup.addViewport(vpId, this.renderingEngineId);
    });
    
    console.log("[Dicom3D] Tools configured");
  }

  render() {
    const { isLoading, error, status, imageCount } = this.state;
    
    const containerStyle = {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gridTemplateRows: '1fr 1fr',
      gap: '4px',
      width: '100%',
      height: '100%',
      padding: '4px',
      boxSizing: 'border-box'
    };
    
    const viewportStyle = {
      width: '100%',
      height: '100%',
      minHeight: '280px',
      position: 'relative',
      border: '1px solid #444',
      boxSizing: 'border-box',
      overflow: 'hidden',
      background: '#000'
    };
    
    const labelStyle = {
      position: 'absolute',
      top: 5,
      left: 5,
      color: 'orange',
      pointerEvents: 'none',
      fontSize: '12px',
      fontWeight: 'bold',
      zIndex: 10,
      textShadow: '1px 1px 2px black'
    };
    
    return (
      <div className="dicom-3d-wrapper" style={{width: '100%', height: '600px', background: '#1a1a1a', color: 'white', position: 'relative'}}>
          {error && (
            <div style={{
              padding: 20, 
              color: '#ff6b6b', 
              zIndex: 100, 
              position: 'absolute', 
              top: 0, 
              left: 0,
              right: 0,
              background: 'rgba(0,0,0,0.95)',
              textAlign: 'center'
            }}>
              <div style={{fontSize: '16px', marginBottom: '10px'}}>⚠️ {error}</div>
              <button 
                onClick={() => {
                  this.setState({ error: null, isLoading: true });
                  this.cleanup();
                  this.setupMPRViewer();
                }}
                style={{
                  padding: '8px 16px',
                  background: '#6c5ce7',
                  border: 'none',
                  color: 'white',
                  cursor: 'pointer',
                  borderRadius: '4px'
                }}
              >
                Retry
              </button>
            </div>
          )}
          
          {isLoading && !error && (
            <div style={{
              padding: 20, 
              zIndex: 100, 
              position: 'absolute', 
              top: 0, 
              left: 0,
              right: 0,
              background: 'rgba(0,0,0,0.8)',
              textAlign: 'center'
            }}>
              <div style={{marginBottom: '8px'}}>{status}</div>
              {imageCount > 0 && (
                <div style={{fontSize: '12px', color: '#888'}}>
                  Processing {imageCount} images
                </div>
              )}
            </div>
          )}
          
          <div style={containerStyle}>
              {/* AXIAL */}
              <div 
                id="axial-viewport-container"
                ref={this.viewportRefs.AXIAL} 
                style={viewportStyle} 
                onContextMenu={e => e.preventDefault()}
              >
                <div style={labelStyle}>{VIEWPORT_CONFIG.AXIAL.label}</div>
              </div>
              
              {/* SAGITTAL */}
              <div 
                id="sagittal-viewport-container"
                ref={this.viewportRefs.SAGITTAL} 
                style={viewportStyle} 
                onContextMenu={e => e.preventDefault()}
              >
                <div style={labelStyle}>{VIEWPORT_CONFIG.SAGITTAL.label}</div>
              </div>
              
              {/* CORONAL */}
              <div 
                id="coronal-viewport-container"
                ref={this.viewportRefs.CORONAL} 
                style={viewportStyle} 
                onContextMenu={e => e.preventDefault()}
              >
                <div style={labelStyle}>{VIEWPORT_CONFIG.CORONAL.label}</div>
              </div>
              
              {/* 3D Placeholder */}
              <div style={{
                ...viewportStyle, 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                color: '#666'
              }}>
                <span>3D View (Coming Soon)</span>
              </div>
          </div>
      </div>
    );
  }
}

const HtxDicom3DView = inject("store")(observer(Dicom3DView));
export { HtxDicom3DView };
