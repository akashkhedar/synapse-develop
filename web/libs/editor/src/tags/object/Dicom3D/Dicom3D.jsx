import React, { Component } from "react";
import { observer, inject } from "mobx-react";
import { 
  RenderingEngine, 
  Enums, 
  volumeLoader, 
  setVolumesForViewports,
  init as initCornerstoneCore,
  setUseCPURendering,
  metaData,
  imageLoader,
  eventTarget,
  EVENTS as CS_EVENTS
} from "@cornerstonejs/core";
import {
  init as initCornerstoneTools,
  addTool,
  ToolGroupManager,
  WindowLevelTool,
  PanTool,
  ZoomTool,
  StackScrollMouseWheelTool,
  TrackballRotateTool,
  Enums as ToolsEnums,
  synchronizers
} from "@cornerstonejs/tools";
import { cornerstoneStreamingImageVolumeLoader } from "@cornerstonejs/streaming-image-volume-loader";
// Flexible Import Strategy
import dicomImageLoaderDefault, { wadouri as wadouriNamed, init as initNamed } from "@cornerstonejs/dicom-image-loader";
import * as cornerstone from "@cornerstonejs/core"; // Required for injection
import dicomParser from "dicom-parser";
import "./Dicom3D.scss";

import { isAlive } from "mobx-state-tree";

// Global Initialization Flag
let isCornerstoneInitialized = false;

async function initCornerstone() {
  if (isCornerstoneInitialized) return;
  
  // Check COOP/COEP
  if (window.crossOriginIsolated) {
      console.log("[Dicom3D] Cross-Origin Isolated: YES (SharedArrayBuffer available)");
  } else {
      console.warn("[Dicom3D] Cross-Origin Isolated: NO (SharedArrayBuffer disabled). Volume Rendering will fail.");
  }

  try {
    // 1. Initialize Core & Tools
    await initCornerstoneCore();
    setUseCPURendering(false); // FORCE GPU
    await initCornerstoneTools();
    
    // 2. Inject Cornerstone into Image Loader (CRITICAL FIX)
    const loader = dicomImageLoaderDefault || {};
    if (loader.external) {
        loader.external.cornerstone = cornerstone;
        loader.external.dicomParser = dicomParser;
        console.log("[Dicom3D] Injected Cornerstone & dicomParser into Image Loader");
    } else {
        try {
             if (dicomImageLoaderDefault) dicomImageLoaderDefault.external = { cornerstone, dicomParser };
        } catch(e) {}
    }

    // 3. Initialize DICOM Image Loader
    const config = { 
        maxWebWorkers: navigator.hardwareConcurrency || 1,
        startWebWorkersOnDemand: true,
        taskConfiguration: {
            decodeTask: {
                initializeCodecsOnStartup: false,
                strict: false,
            }
        }
    };
    
    const initFunc = initNamed || (loader.init);
    
    if (initFunc) {
        await initFunc(config);
    } else {
        if (loader.configure) loader.configure({ useWebWorkers: true, decodeTask: config.taskConfiguration.decodeTask });
        if (loader.webWorkerManager) loader.webWorkerManager.initialize(config);
    }

    // 4. Register Volume Loader
    try {
        volumeLoader.registerVolumeLoader(
            "cornerstoneStreamingImageVolume",
            cornerstoneStreamingImageVolumeLoader
        );
    } catch(e) {/* ignore */}

    // 5. Register Image Loader for 'wadouri' scheme
    const wadouriLib = wadouriNamed || (loader.wadouri);
    
    if (wadouriLib) {
        imageLoader.registerImageLoader('wadouri', wadouriLib.loadImage);
        imageLoader.registerImageLoader('dicomfile', wadouriLib.loadImage); 
    } 
    
    // 6. Register Tools
    [
        WindowLevelTool, 
        PanTool, 
        ZoomTool, 
        StackScrollMouseWheelTool,
        TrackballRotateTool 
    ].forEach(Tool => {
        try { addTool(Tool); } catch(e){}
    });

    isCornerstoneInitialized = true;
    console.log("[Dicom3D] System Initialized");

  } catch (error) {
    console.error("Failed to initialize Cornerstone3D:", error);
  }
}

class Dicom3DView extends Component {
  constructor(props) {
    super(props);
    this.elementAxial = React.createRef();
    this.elementSagittal = React.createRef();
    this.elementCoronal = React.createRef();
    this.element3D = React.createRef(); // New 3D Viewport

    this.unmounted = false;
    
    this.renderingEngineId = `engine-${Math.random().toString(36).substr(2, 6)}`;
    this.toolGroupId = `group-${Math.random().toString(36).substr(2, 6)}`;
    this.toolGroup3DId = `group-3d-${Math.random().toString(36).substr(2, 6)}`; // Separate group for 3D
    
    this.state = {
      isLoading: true,
      error: null,
      status: 'Initializing...'
    };
    
    this.renderingEngine = null;
    this.volumeId = null;
    this.customProvider = null;
  }

  async componentDidMount() {
    this.unmounted = false;
    await initCornerstone();
    if (this.unmounted) return;
    this.processData();
  }

  componentWillUnmount() {
    this.unmounted = true;
    if (this.renderingEngine) {
        this.renderingEngine.destroy();
        this.renderingEngine = null;
    }
    if (this.synchronizers) {
        this.synchronizers.forEach(s => s.destroy());
    }
    if (this.customProvider) {
        metaData.removeProvider(this.customProvider);
    }
    ToolGroupManager.destroyToolGroup(this.toolGroupId);
    ToolGroupManager.destroyToolGroup(this.toolGroup3DId);
  }

  async loadVolume(zipUrl) {
      console.log(`[Dicom3D] Requesting processing for ZIP: ${zipUrl}`);
      this.setState({ status: 'Processing on server...' });

      // Call new backend API
      const apiUrl = `/api/import/dicom-process/?url=${encodeURIComponent(zipUrl)}`;
      
      let response;
      try {
        response = await fetch(apiUrl);
      } catch (err) {
        throw new Error(`Connection Error: ${err.message}`);
      }
      
      if (!response.ok) {
          const text = await response.text();
          let msg = text;
          try { msg = JSON.parse(text).error; } catch(e){}
          throw new Error(msg || `Server Error: ${response.status}`);
      }

      const data = await response.json();
      const serverImageIds = data.imageIds;
      
      if (!serverImageIds || serverImageIds.length === 0) {
          throw new Error("No DICOM images returned from server");
      }

      console.log(`[Dicom3D] Server returned ${serverImageIds.length} images`);
      this.setState({ status: 'streaming metadata...' });

      // Prefix with 'wadouri:' for Cornerstone Image Loader
      // Assuming server returns relative paths like /data/..., prepend current origin if needed
      // But wadouri handles relative URLs fine.
      const imageIds = serverImageIds.map(url => `wadouri:${url}`);
      return imageIds;
  }

  async processData() {
    try {
        if (this.unmounted) return;
        
        // Safety Check
        if (!this.elementAxial.current || !this.element3D.current) {
            console.warn("Viewports not ready in DOM. Retrying...");
            setTimeout(() => this.processData(), 100);
            return;
        }

        const { item } = this.props;
        if (!isAlive(item)) return;

        const zipUrl = item.parsedValue;
        let imageIds = [];

        // 1. Get Image IDs from Server
        if (zipUrl && zipUrl.endsWith('.zip')) {
            imageIds = await this.loadVolume(zipUrl);
        } else {
            throw new Error("Please provide a ZIP file for 3D Demo");
        }
        
        if (this.unmounted) return;

        // 2. Setup Rendering Engine
        if (this.renderingEngine) {
            this.renderingEngine.destroy();
            this.renderingEngine = null;
        }
        
        this.setState({ status: 'Setting up Viewports...' });
        this.renderingEngine = new RenderingEngine(this.renderingEngineId);

        const viewportInput = [
            {
                viewportId: "AXIAL",
                type: Enums.ViewportType.ORTHOGRAPHIC,
                element: this.elementAxial.current,
                defaultOptions: { orientation: Enums.OrientationAxis.AXIAL }
            },
            {
                viewportId: "SAGITTAL",
                type: Enums.ViewportType.ORTHOGRAPHIC,
                element: this.elementSagittal.current,
                defaultOptions: { orientation: Enums.OrientationAxis.SAGITTAL }
            },
            {
                viewportId: "CORONAL",
                type: Enums.ViewportType.ORTHOGRAPHIC,
                element: this.elementCoronal.current,
                defaultOptions: { orientation: Enums.OrientationAxis.CORONAL }
            },
            {
                viewportId: "VOLUME_3D",
                type: Enums.ViewportType.VOLUME_3D,
                element: this.element3D.current,
                defaultOptions: { orientation: Enums.OrientationAxis.AXIAL } 
            }
        ];

        this.renderingEngine.setViewports(viewportInput);

        // 3. Create Volume
        this.volumeId = `cornerstoneStreamingImageVolume:vol-${Math.random().toString(36).substr(2,6)}`;
        
        this.setState({ status: 'Creating Volume...' });
        
        // Define volume with progressive rendering
        const volume = await volumeLoader.createAndCacheVolume(this.volumeId, {
            imageIds: imageIds
        });
        
        if (this.unmounted) return;

        // 4. Setup ToolGroups
        this.setupTools();
        this.setupSynchronizers();

        // 5. Load Volume Data
        // This triggers the streaming
        volume.load();

        // 6. Set Volume to Viewports
        // Render Axial first for better UX
        await setVolumesForViewports(
            this.renderingEngine, 
            [{ volumeId: this.volumeId }], 
            ["AXIAL"]
        );
        this.renderingEngine.render();
        
        // Then add others
        await setVolumesForViewports(
            this.renderingEngine, 
            [{ volumeId: this.volumeId }], 
            ["SAGITTAL", "CORONAL", "VOLUME_3D"]
        );
        
        if (this.unmounted) return;

        // 7. Render All
        this.renderingEngine.render();
        this.setState({ isLoading: false, status: 'Ready' });

        // Apply visual presets to 3D volume
        const viewport3D = this.renderingEngine.getViewport("VOLUME_3D");
        // viewport3D.setProperties({ preset: 'CT-Bone' }); // Example if available

    } catch (err) {
        console.error("Dicom3D Error:", err);
        if (!this.unmounted) {
             this.setState({ error: err.message, isLoading: false });
        }
    }
  }

  setupSynchronizers() {
      if (this.synchronizers) {
          this.synchronizers.forEach(s => s.destroy());
          this.synchronizers = null;
      }

      const cameraSyncId = `${this.toolGroupId}-camera`;
      const voiSyncId = `${this.toolGroupId}-voi`;

      const cameraSynchronizer = synchronizers.createCameraPositionSynchronizer(cameraSyncId);
      const voiSynchronizer = synchronizers.createVOISynchronizer(voiSyncId);

      // Sync the Orthographic views
      ["AXIAL", "SAGITTAL", "CORONAL"].forEach(viewportId => {
          cameraSynchronizer.add({ renderingEngineId: this.renderingEngineId, viewportId });
          voiSynchronizer.add({ renderingEngineId: this.renderingEngineId, viewportId });
      });
      // Do NOT sync camera of 3D view with 2D views usually, but VOI is okay
      voiSynchronizer.add({ renderingEngineId: this.renderingEngineId, viewportId: "VOLUME_3D" });
      
      this.synchronizers = [cameraSynchronizer, voiSynchronizer];
  }

  setupTools() {
      ToolGroupManager.destroyToolGroup(this.toolGroupId);
      ToolGroupManager.destroyToolGroup(this.toolGroup3DId);
      
      const toolGroup = ToolGroupManager.createToolGroup(this.toolGroupId);
      const toolGroup3D = ToolGroupManager.createToolGroup(this.toolGroup3DId);
      
      // MPR Tools
      toolGroup.addTool(WindowLevelTool.toolName);
      toolGroup.addTool(PanTool.toolName);
      toolGroup.addTool(ZoomTool.toolName);
      toolGroup.addTool(StackScrollMouseWheelTool.toolName);

      // 3D Tools
      toolGroup3D.addTool(TrackballRotateTool.toolName);
      toolGroup3D.addTool(ZoomTool.toolName);
      toolGroup3D.addTool(PanTool.toolName);
      toolGroup3D.addTool(WindowLevelTool.toolName);

      // Configure MPR Bindings
      toolGroup.setToolActive(WindowLevelTool.toolName, { bindings: [{ mouseButton: ToolsEnums.MouseBindings.Primary }] });
      toolGroup.setToolActive(PanTool.toolName, { bindings: [{ mouseButton: ToolsEnums.MouseBindings.Auxiliary }] });
      toolGroup.setToolActive(ZoomTool.toolName, { bindings: [{ mouseButton: ToolsEnums.MouseBindings.Secondary }] });
      toolGroup.setToolActive(StackScrollMouseWheelTool.toolName);

      // Configure 3D Bindings
      toolGroup3D.setToolActive(TrackballRotateTool.toolName, { bindings: [{ mouseButton: ToolsEnums.MouseBindings.Primary }] });
      toolGroup3D.setToolActive(PanTool.toolName, { bindings: [{ mouseButton: ToolsEnums.MouseBindings.Auxiliary }] });
      toolGroup3D.setToolActive(ZoomTool.toolName, { bindings: [{ mouseButton: ToolsEnums.MouseBindings.Secondary }] });

      // Apply to Viewports
      toolGroup.addViewport("AXIAL", this.renderingEngineId);
      toolGroup.addViewport("SAGITTAL", this.renderingEngineId);
      toolGroup.addViewport("CORONAL", this.renderingEngineId);
      
      toolGroup3D.addViewport("VOLUME_3D", this.renderingEngineId);
  }

  render() {
    const { isLoading, error, status } = this.state;
    // 2x2 Grid Layout
    const gridStyle = { width: '50%', height: '50%', display: 'inline-block', position: 'relative', border: '1px solid #333', boxSizing: 'border-box' };
    
    return (
      <div className="dicom-3d-wrapper" style={{width: '100%', height: '600px', background: 'black', color: 'white'}}>
          {error ? <div style={{padding:20, color:'red', zIndex:10, position:'absolute'}}>Error: {error}</div> :
           isLoading ? <div style={{padding:20, zIndex:10, position:'absolute'}}>{status}</div> : null}
          
          <div style={{width:'100%', height: '100%'}}>
              <div ref={this.elementAxial} style={gridStyle} onContextMenu={e=>e.preventDefault()}/>
              <div ref={this.elementSagittal} style={gridStyle} onContextMenu={e=>e.preventDefault()}/>
              <div ref={this.elementCoronal} style={gridStyle} onContextMenu={e=>e.preventDefault()}/>
              <div ref={this.element3D} style={gridStyle} onContextMenu={e=>e.preventDefault()}>
                   <div style={{position:'absolute', top:5, right:5, color:'lime', fontSize:12, pointerEvents:'none'}}>3D VOLUME</div>
              </div>
          </div>
      </div>
    );
  }
}

const HtxDicom3DView = inject("store")(observer(Dicom3DView));
export { HtxDicom3DView };
