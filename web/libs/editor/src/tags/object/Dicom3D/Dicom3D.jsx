import React, { Component } from "react";
import { observer, inject } from "mobx-react";
import { types } from "mobx-state-tree";
import Registry from "../../../core/Registry";
import { 
  RenderingEngine, 
  Enums, 
  volumeLoader, 
  setVolumesForViewports,
  init as initCornerstoneCore 
} from "@cornerstonejs/core";
import {
  init as initCornerstoneTools,
  addTool,
  ToolGroupManager,
  WindowLevelTool,
  PanTool,
  ZoomTool,
  Enums as ToolsEnums
} from "@cornerstonejs/tools";
import { cornerstoneStreamingImageVolumeLoader } from "@cornerstonejs/core";
import JSZip from "jszip";
import "./Dicom3D.scss";

// Initialize Cornerstone3D
let isCornerstoneInitialized = false;

async function initCornerstone() {
  if (isCornerstoneInitialized) return;

  try {
    // Initialize Core and Tools
    await initCornerstoneCore();
    await initCornerstoneTools();

    // Register Tools
    addTool(WindowLevelTool);
    addTool(PanTool);
    addTool(ZoomTool);

    
    isCornerstoneInitialized = true;
  } catch (error) {
    console.error("Failed to initialize Cornerstone3D:", error);
  }
}

class Dicom3DView extends Component {
  constructor(props) {
    super(props);
    this.elementRef = React.createRef();
    this.renderingEngineId = `my-rendering-engine-${Math.random().toString(36).substr(2, 9)}`;
    this.viewportId = "CT_AXIAL_STACK"; 
    this.toolGroupId = "my-tool-group";
    this.state = {
      isLoading: true,
      dataProgress: 0,
      processingStatus: 'Initializing...',
      error: null
    };
    this.createdObjectUrls = []; // Track for cleanup
  }

  async componentDidMount() {
    await initCornerstone();
    this.initViewport();
  }

  componentWillUnmount() {
    // Clean up Cornerstone
    const renderingEngine = new RenderingEngine(this.renderingEngineId);
    renderingEngine.destroy();
    
    // Clean up Blob URLs
    this.createdObjectUrls.forEach(url => URL.revokeObjectURL(url));
    this.createdObjectUrls = [];
  }

  async initViewport() {
    const element = this.elementRef.current;
    if (!element) return;

    try {
      const { item } = this.props;
      let values = item.parsedValue;
      if (!Array.isArray(values)) values = [values];

      let imageIds = [];

      // Check if it's a single ZIP file
      if (values.length === 1 && typeof values[0] === 'string' && values[0].toLowerCase().endsWith('.zip')) {
          this.setState({ processingStatus: 'Downloading ZIP...' });
          imageIds = await this.processZipFile(values[0]);
      } else {
          // Standard List Processing
          imageIds = values.map(val => {
            let url = val;
            if (url && url.startsWith('/')) {
                url = window.location.origin + url;
            }
            if (url && !url.startsWith('wadouri:') && !url.startsWith('dicomweb:')) {
                url = 'wadouri:' + url;
            }
            return url;
          });
      }

      if (imageIds.length === 0) {
        throw new Error("No image IDs found");
      }

      this.setState({ processingStatus: 'Creating Volume...' });

      // Instantiate Rendering Engine
      const renderingEngine = new RenderingEngine(this.renderingEngineId);

      // Create Volume Viewport Input
      const viewportInput = {
        viewportId: this.viewportId,
        type: Enums.ViewportType.ORTHOGRAPHIC,
        element: element,
        defaultOptions: {
          orientation: Enums.OrientationAxis.AXIAL,
          background: [0, 0, 0],
        },
      };

      renderingEngine.enableElement(viewportInput);

      // Define Volume
      const volumeName = 'CT_VOLUME_ID:' + Math.random().toString(36).substr(2, 9);
      const volumeId = `${volumeName}`; 
      
      const volume = await volumeLoader.createAndCacheVolume(volumeId, {
        imageIds,
      });

      // Load the volume
      volume.load((event) => {
          // Optional: Track loading progress if Cornerstone exposes it here or via events
      });

      // Set Volume to Viewport
      await setVolumesForViewports(renderingEngine, [{ volumeId }], [this.viewportId]);

      // Render
      renderingEngine.render();

      this.setupTools();

      this.setState({ isLoading: false, processingStatus: 'Ready' });

    } catch (err) {
      console.error("Error initializing 3D viewport:", err);
      this.setState({ error: err.message, isLoading: false, processingStatus: 'Error' });
    }
  }

  async processZipFile(zipUrl) {
      // Resolve relative URL
      if (zipUrl.startsWith('/')) {
          zipUrl = window.location.origin + zipUrl;
      }

      const response = await fetch(zipUrl, { credentials: 'include' });
      if (!response.ok) throw new Error(`Failed to fetch ZIP: ${response.statusText}`);
      
      const blob = await response.blob();
      const zip = await JSZip.loadAsync(blob);
      
      const filePromises = [];
      const imageIds = [];

      this.setState({ processingStatus: 'Extracting DICOMs...' });

      // Sort files to ensure order (optional but good for CT)
      // We'll rely on Cornerstone to sort by Instance Number, but sorting filenames helps if Metadata is missing
      const filenames = Object.keys(zip.files).sort();

      for (const filename of filenames) {
          const file = zip.files[filename];
          if (!file.dir && !filename.includes('__MACOSX') && !filename.endsWith('.json')) {
             // Heuristic: Process non-directory, non-system files
             // We can check magic number later or let Cornerstone fail on bad files
             const promise = file.async('blob').then(fileBlob => {
                 const objectUrl = URL.createObjectURL(fileBlob);
                 this.createdObjectUrls.push(objectUrl);
                 return "wadouri:" + objectUrl;
             });
             filePromises.push(promise);
          }
      }

      const ids = await Promise.all(filePromises);
      return ids;
  }

  setupTools() {
    // Define Tool Group
    let toolGroup = ToolGroupManager.getToolGroup(this.toolGroupId);
    if (!toolGroup) {
      toolGroup = ToolGroupManager.createToolGroup(this.toolGroupId);
    }

    // Add Tools to Group
    toolGroup.addTool(WindowLevelTool.toolName);
    toolGroup.addTool(PanTool.toolName);
    toolGroup.addTool(ZoomTool.toolName);
    toolGroup.addTool(ZoomTool.toolName);

    // Set Tool States
    toolGroup.setToolActive(WindowLevelTool.toolName, {
      bindings: [
        {
          mouseButton: ToolsEnums.MouseBindings.Primary, // Left Click
        },
      ],
    });
    toolGroup.setToolActive(PanTool.toolName, {
      bindings: [
        {
          mouseButton: ToolsEnums.MouseBindings.Auxiliary, // Middle Click
        },
        {
            mouseButton: ToolsEnums.MouseBindings.Secondary, // Right Click (Standard)
        }
      ],
    });
    toolGroup.setToolActive(ZoomTool.toolName, {
      bindings: [
        {
          mouseButton: ToolsEnums.MouseBindings.Secondary, // Right Click (Alternative)
          modifierKey: ToolsEnums.KeyboardBindings.Ctrl,
        },
      ],
    });
    
    // Stack Scroll (Mouse Wheel) works for Volumes too (moves through slices)
    // toolGroup.setToolActive(StackScrollMouseWheelTool.toolName);

    // Apply Group to Viewport
    toolGroup.addViewport(this.viewportId, this.renderingEngineId);
  }

  render() {
    const { item } = this.props;
    const { isLoading, error, processingStatus } = this.state;

    return (
      <div 
        className="dicom-3d-container" 
        style={{ width: item.width || "100%", height: item.height || "512px" }}
      >
        <div 
            ref={this.elementRef} 
            className="viewport-element"
            onContextMenu={(e) => e.preventDefault()}
        />
        
        {isLoading && (
            <div className="loading-overlay">
                <div style={{textAlign: 'center'}}>
                    <div style={{fontSize: '1.2em', marginBottom: '10px'}}>{processingStatus}</div>
                    <div className="spinner"></div> 
                </div>
            </div>
        )}
        
        {error && (
            <div className="loading-overlay" style={{background: 'rgba(50,0,0,0.8)'}}>
                Error: {error}
            </div>
        )}
      </div>
    );
  }
}

const HtxDicom3DView = inject("store")(observer(Dicom3DView));

export { HtxDicom3DView };
