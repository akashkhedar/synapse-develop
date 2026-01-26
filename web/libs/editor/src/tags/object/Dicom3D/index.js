import { Dicom3DModel } from "./Dicom3D";
import { HtxDicom3DView } from "./Dicom3D.jsx";
import Registry from "../../../core/Registry";

Registry.addTag("dicom3d", Dicom3DModel, HtxDicom3DView);
Registry.addObjectType(Dicom3DModel);

export { Dicom3DModel, HtxDicom3DView };
