import Registry from "../../../core/Registry";
import DicomModel from "./Dicom";
import { HtxDicomView } from "./Dicom.jsx";

Registry.addTag("dicom", DicomModel, HtxDicomView);
Registry.addObjectType(DicomModel);

export { DicomModel, HtxDicomView };
