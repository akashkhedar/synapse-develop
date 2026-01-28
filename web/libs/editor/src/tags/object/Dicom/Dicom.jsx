import React, { Component } from "react";
import { observer, inject } from "mobx-react";
import Registry from "../../../core/Registry";
import DicomModel from "./Dicom";
import { HtxDicom3DView } from "../Dicom3D/Dicom3D.jsx";
import "./Dicom.scss";

// Legacy Dicom.jsx has been replaced by Dicom3D redirection 
// to support the migration to @cornerstonejs (Cornerstone3D).
// All DICOM usage now routes through the 3D Volume Viewport.

const DicomView = observer(({ item }) => {
  return <HtxDicom3DView item={item} />;
});

const HtxDicomView = inject("store")(DicomView);

Registry.addTag("dicom", DicomModel, HtxDicomView);
Registry.addObjectType(DicomModel);

export { HtxDicomView };
