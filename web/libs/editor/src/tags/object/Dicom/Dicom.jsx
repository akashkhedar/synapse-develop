import React, { Component } from "react";
import { observer, inject } from "mobx-react";
import { reaction } from "mobx";
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

console.log("Dicom.jsx file evaluated");

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

            // Define Stack for Segmentation (Required by Cornerstone Tools)
            const stack = {
                currentImageIdIndex: 0,
                imageIds: [imageId]
            };
            cornerstoneTools.addToolState(element, 'stack', stack);
            
            // --- TOOL SETUP ---
            // Register Tools
            const WwwcTool = cornerstoneTools.WwwcTool;
            const PanTool = cornerstoneTools.PanTool;
            const ZoomTool = cornerstoneTools.ZoomTool;
            const ZoomMouseWheelTool = cornerstoneTools.ZoomMouseWheelTool;
            const StackScrollTool = cornerstoneTools.StackScrollTool;
            const BrushTool = cornerstoneTools.BrushTool;
            const FreehandRoiTool = cornerstoneTools.FreehandRoiTool;

            cornerstoneTools.addToolForElement(element, WwwcTool);
            cornerstoneTools.addToolForElement(element, PanTool);
            cornerstoneTools.addToolForElement(element, ZoomTool);
            cornerstoneTools.addToolForElement(element, ZoomMouseWheelTool);
            cornerstoneTools.addToolForElement(element, StackScrollTool);
            cornerstoneTools.addToolForElement(element, BrushTool);
            cornerstoneTools.addToolForElement(element, FreehandRoiTool);

            // ACTIVATION HELPER: Ensures Base Navigation Tools are ALWAYS active
            const activateBaseTools = () => {
                cornerstoneTools.setToolActiveForElement(element, 'Pan', { mouseButtonMask: 2 }); // Right Click
                cornerstoneTools.setToolActiveForElement(element, 'ZoomMouseWheel', { }); // Mouse Wheel
            };

            // INITIAL STATE
            activateBaseTools();
            // Default Left Click -> Wwwc (Window/Level)
            cornerstoneTools.setToolActiveForElement(element, 'Wwwc', { mouseButtonMask: 1 });
            
            // --- SEGMENTATION SUPPORT ---
            const segmentationModule = cornerstoneTools.getModule('segmentation');
            segmentationModule.configuration.drawAlpha = 0.5;
            segmentationModule.configuration.renderFill = true;

            // Initialize segmentation state for this element
            // We need to ensure the element has a `toolState` for segmentation or force create it
            // Typically adding BrushTool handles some of this, but setting active index might fail if empty.
            
            // Ensure state exists
            const { state } = segmentationModule;
             if (!state.series[0]) {
                 state.series[0] = {
                     labelmaps: []
                 };
             }
            
             // We generally don't need to manually set activeLabelmapIndex immediately if we don't have a labelmap yet?
             // But BrushTool needs one created.
             // Let's defer setting active index until we are sure or try-catch it.
             
             try {
                // Force creation of a labelmap 0 ??
                // Actually, BrushTool will create it on use if not present.
                // But let's try to set it if we can.
                // segmentationModule.setters.activeLabelmapIndex(element, 0); 
                // Commented out to avoid crash on init. Let BrushTool handle it.
             } catch(e) { console.warn("Could not set active labelmap index", e); }

            // BrushTool already declared/added above
            // cornerstoneTools.addToolForElement(element, BrushTool); // Removed duplicate

            // Sync with Label Studio state
            // When a label is selected, LS activates the Brush tool (internal).
            // We observe this and switch Cornerstone tool from Wwwc to Brush.
            const mobx = require("mobx");
            
            // Sync with Label Studio state
            // Switch to Brush Tool if ANY label connected to this DICOM is selected.
            
            console.log("[Dicom] Setting up tool sync reaction...");
            
            this.disposeReaction = reaction(
                () => {
                    let activeLabel = null;
                    let activeIndex = 1;
                    
                    if (item.annotation && item.annotation.names) {
                        let idx = 1;
                        // We iterate to find which label is selected
                        // We also need a consistent index for each label to keep segments separate
                        // Assuming the order of keys in the map is consistent or we use the defined order in XML
                        // Map iteration order is insertion order, usually consistent for template.
                        
                        item.annotation.names.forEach((tag) => {
                             if (tag.type.endsWith('labels') && tag.toname === item.name) {
                                  // Iterate children of the specific Labels tag
                                  // BUT 'tag' here IS the Labels component? No, item.annotation.names values are Tags (Models)
                                  // The 'tag' is the BrushLabels model.
                                  // It has 'children' which are the Label models.
                                  tag.children.forEach((label, childIdx) => {
                                      const currentSegmentIndex = childIdx + 1; 

                                      if (label.selected) {
                                          activeLabel = {
                                              name: label.value,
                                              color: label.background, 
                                              index: currentSegmentIndex,
                                              type: tag.type.includes('brush') ? 'brush' : 'polygon'
                                          };
                                      }
                                  });
                             }
                        });
                    }
                    return activeLabel;
                },
                (activeLabel) => {
                    console.log(`[Dicom] Tool switch. Active Label:`, activeLabel);
                    
                    // Deactivate Left-Click Tools (avoid conflicts)
                    try {
                        cornerstoneTools.setToolPassiveForElement(element, 'Wwwc');
                        cornerstoneTools.setToolPassiveForElement(element, 'Brush');
                        cornerstoneTools.setToolPassiveForElement(element, 'FreehandRoi');
                    } catch(e) {}

                    if (activeLabel) {
                        try {
                            if (activeLabel.type === 'brush') {
                                cornerstoneTools.setToolActiveForElement(element, 'Brush', { mouseButtonMask: 1 });
                                
                                const { setters, state } = cornerstoneTools.getModule('segmentation');
                                setters.activeSegmentIndex(element, activeLabel.index);
                                
                                // Set Color
                                const hex = activeLabel.color;
                                const r = parseInt(hex.slice(1, 3), 16);
                                const g = parseInt(hex.slice(3, 5), 16);
                                const b = parseInt(hex.slice(5, 7), 16);
                                
                                let activeLabelmapIndex = state.series[0] ? state.series[0].activeLabelmapIndex : 0;
                                if (!state.series[0]) state.series[0] = { labelmaps: [] };
                                
                                if (state.series[0].labelmaps[activeLabelmapIndex]) {
                                    const colorLutIndex = state.series[0].labelmaps[activeLabelmapIndex].colorLUTIndex;
                                    const colorLut = state.colorLutTables[colorLutIndex];
                                    if (colorLut) {
                                        colorLut[activeLabel.index] = [r, g, b, 255];
                                        setters.colorLutTables(element, state.colorLutTables);
                                    }
                                }
                                
                            } else if (activeLabel.type === 'polygon') {
                                cornerstoneTools.setToolActiveForElement(element, 'FreehandRoi', { mouseButtonMask: 1 });
                                cornerstoneTools.toolColors.setToolColor(activeLabel.color);
                                
                                // Freehand Config
                                const freehandTool = cornerstoneTools.getToolForElement(element, 'FreehandRoi');
                                if (freehandTool) {
                                    freehandTool.configuration.alwaysShowStats = false; 
                                    freehandTool.configuration.showScanStats = false; 
                                    freehandTool.configuration.renderFill = true;
                                    freehandTool.configuration.fillOpacity = 0.5;
                                    freehandTool.configuration.getTextCallback = () => [];
                                }

                                const handleMeasurementEvent = (evt) => {
                                    if (evt.detail.toolName === 'FreehandRoi') {
                                        const measurementData = evt.detail.measurementData;
                                        measurementData.color = activeLabel.color;
                                        // Hide text
                                        if (measurementData.textBox) {
                                            measurementData.textBox.visible = false;
                                            measurementData.textBox.x = -5000;
                                            measurementData.textBox.y = -5000;
                                        }
                                        cornerstone.updateImage(element);
                                    }
                                };
                                element.removeEventListener(cornerstoneTools.EVENTS.MEASUREMENT_ADDED, handleMeasurementEvent);
                                element.addEventListener(cornerstoneTools.EVENTS.MEASUREMENT_ADDED, handleMeasurementEvent);
                            }
                        } catch (e) {
                             console.error("Error activating segmentation tool:", e);
                        }
                    } else {
                        // Revert to Wwwc if no label selected
                        try {
                            cornerstoneTools.setToolActiveForElement(element, 'Wwwc', { mouseButtonMask: 1 });
                        } catch (e) {}
                    }
                    
                    // ALWAYS restore Base Tools (Right Click Pan, Wheel Zoom)
                    activateBaseTools();
                    
                    cornerstone.updateImage(element);
                },
                { fireImmediately: true }
            );

            // Force Cursor Style
            // Cornerstone often resets cursor, so we force it on mousemove
            this.onMouseMove = () => {
                if (element.style.cursor !== 'crosshair') {
                    element.style.setProperty('cursor', 'crosshair', 'important');
                }
            };
            element.addEventListener('mousemove', this.onMouseMove);

            // Brush Size Shortcuts
            this.onKeyDown = (e) => {
                if (e.key === '[' || e.key === ']') {
                    const module = cornerstoneTools.getModule('segmentation');
                    let radius = module.getters.radius(element);
                    if (e.key === '[') radius = Math.max(1, radius - 2);
                    if (e.key === ']') radius += 2;
                    module.setters.radius(element, radius);
                    cornerstone.updateImage(element);
                }
            };
            window.addEventListener('keydown', this.onKeyDown);

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
    if (this.disposeReaction) {
        this.disposeReaction();
    }
    if (this.onKeyDown) {
        window.removeEventListener('keydown', this.onKeyDown);
    }
  }

  render() {
    const { item } = this.props;
    return (
      <div className="dicom-viewer-container" style={{ width: item.width || "100%", height: item.height || "512px", position: "relative", color: "white" }}>
        <div 
          ref={this.element} 
          className="cornerstone-element" 
          style={{ width: "100%", height: "100%", cursor: "crosshair" }}
          onContextMenu={(e) => e.preventDefault()}
        />
      </div>
    );
  }
}

// Update initViewer to include Brush
// We need to move logic into initViewer or componentDidMount

const HtxDicomView = inject("store")(observer(DicomView));

Registry.addTag("dicom", DicomModel, HtxDicomView);
Registry.addObjectType(DicomModel);

export { HtxDicomView };
