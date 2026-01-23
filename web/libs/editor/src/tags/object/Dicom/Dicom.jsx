import React, { Component } from "react";
import { observer, inject } from "mobx-react";
import { types } from "mobx-state-tree";
import Registry from "../../../core/Registry";
import DicomModel from "./Dicom";
import cornerstone from "cornerstone-core";
import cornerstoneTools from "cornerstone-tools";
import cornerstoneWADOImageLoader from "cornerstone-wado-image-loader";
import dicomParser from "dicom-parser";
import cornerstoneMath from "cornerstone-math";
import Hammer from "hammerjs";
import "./Dicom.scss";

// Initialize cornerstone tools and loader outside the component to avoid re-init
let isCornerstoneInitialized = false;

function initCornerstone() {
  if (isCornerstoneInitialized) return;

  cornerstoneTools.external.cornerstone = cornerstone;
  cornerstoneTools.external.Hammer = Hammer;
  cornerstoneTools.external.cornerstoneMath = cornerstoneMath;
  
  cornerstoneWADOImageLoader.external.cornerstone = cornerstone;
  cornerstoneWADOImageLoader.external.dicomParser = dicomParser;
  
  // Configure WADO Image Loader
  cornerstoneWADOImageLoader.webWorkerManager.initialize({
    maxWebWorkers: navigator.hardwareConcurrency || 1,
    startWebWorkersOnDemand: true,
    taskConfiguration: {
        decodeTask: {
            initializeCodecsOnStartup: false,
            usePDFJS: false,
            strict: false,
            codecsPath: 'https://unpkg.com/cornerstone-wado-image-loader@3.3.1/dist/cornerstoneWADOImageLoaderWebWorker.min.js'
        },
    },
    webWorkerPath: 'https://unpkg.com/cornerstone-wado-image-loader@3.3.1/dist/cornerstoneWADOImageLoaderWebWorker.min.js',
  });

  cornerstoneTools.init({
    globalToolSyncEnabled: false,
    showSVGCursors: true
  });
  isCornerstoneInitialized = true;
}

class DicomView extends Component {
  constructor(props) {
    super(props);
    this.element = React.createRef();
  }

  componentDidMount() {
    initCornerstone();
    this.initViewer();
  }

  initViewer() {
    const element = this.element.current;
    if (!element) return;

    cornerstone.enable(element);

    const { item } = this.props;
    // Assuming item.value is a URL to the DICOM file
    // WADO Image Loader expects 'wadouri:' prefix for HTTP GET
    let imageId = item.parsedValue;
    
    // Add wadouri prefix if missing and it looks like a url
    if (imageId) {
        // Resolve relative paths
        if (imageId.startsWith('/')) {
            imageId = window.location.origin + imageId;
        }

        if (!imageId.startsWith('wadouri:') && !imageId.startsWith('dicomweb:')) {
            imageId = 'wadouri:' + imageId;
        }
    }

    if (imageId) {
      cornerstone.loadImage(imageId).then(image => {
        const element = this.element.current;
        // Check if component is still mounted and element exists
        if (!element) return;
        
        try {
            // Re-enable in case it was disabled or not enabled correctly
            // cornerstone.getEnabledElement throws if not enabled
            try {
                cornerstone.getEnabledElement(element);
            } catch(e) {
                cornerstone.enable(element);
            }

            cornerstone.displayImage(element, image);
            
            // Enable default tools
            const WwwcTool = cornerstoneTools.WwwcTool;
            const PanTool = cornerstoneTools.PanTool;
            const ZoomTool = cornerstoneTools.ZoomTool;
            const ZoomMouseWheelTool = cornerstoneTools.ZoomMouseWheelTool;

            // Clear previous tool state to avoid duplicates if re-rendering
            cornerstoneTools.clearToolState(element, 'Wwwc');
            cornerstoneTools.clearToolState(element, 'Pan');
            cornerstoneTools.clearToolState(element, 'Zoom');

            cornerstoneTools.addToolForElement(element, WwwcTool);
            cornerstoneTools.addToolForElement(element, PanTool);
            cornerstoneTools.addToolForElement(element, ZoomTool);
            cornerstoneTools.addToolForElement(element, ZoomMouseWheelTool);

            cornerstoneTools.setToolActiveForElement(element, 'Wwwc', { mouseButtonMask: 1 }); // Left click
            cornerstoneTools.setToolActiveForElement(element, 'Pan', { mouseButtonMask: 2 }); // Middle click
            cornerstoneTools.setToolActiveForElement(element, 'Zoom', { mouseButtonMask: 4 }); // Right click
            cornerstoneTools.setToolActiveForElement(element, 'ZoomMouseWheel', { });
            
            // Notify MobX generic readiness
            item.setReady(true);
        } catch (err) {
            console.error("Error setting up Cornerstone:", err);
        }
      }).catch(err => {
        console.error("Error loading DICOM:", err);
        const element = this.element.current;
        if (element) {
             element.innerHTML = `<div style="color:red; padding: 20px;">Error loading DICOM: ${err.message}</div>`;
        }
      });
    }
  }

  componentWillUnmount() {
    const element = this.element.current;
    if (element) {
      cornerstone.disable(element);
    }
  }

  render() {
    const { item } = this.props;
    const style = {
      width: item.width || "100%",
      height: item.height || "512px",
      position: "relative",
      color: "white" // Text color inside canvas
    };

    return (
      <div className="dicom-viewer-container" style={style}>
        <div 
          ref={this.element} 
          className="cornerstone-element" 
          style={{ width: "100%", height: "100%" }}
          onContextMenu={(e) => e.preventDefault()}
        />
      </div>
    );
  }
}

const HtxDicomView = inject("store")(observer(DicomView));

Registry.addTag("dicom", DicomModel, HtxDicomView);
Registry.addObjectType(DicomModel);

export { HtxDicomView };
