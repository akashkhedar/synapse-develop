import dicomParser from "dicom-parser";

/**
 * Robustly parses a DICOM byte array and returns standard metadata 
 * expected by Cornerstone3D.
 * 
 * @param {Uint8Array} byteArray - The DICOM file data
 * @param {string} imageId - The cornerstone imageId
 * @returns {object} Metadata object
 */
export function getDicomMetadata(byteArray, imageId) {
    let dataSet;
    try {
        dataSet = dicomParser.parseDicom(byteArray);
    } catch(e) {
        console.error("Failed to parse DICOM header:", e);
        return null;
    }

    const { string, uint16, text } = dataSet;

    // Helper to get float array string and parse it
    const getFloatArray = (tag) => {
        const val = string(tag);
        return val ? val.split('\\').map(parseFloat) : [];
    };

    // Helper to safely get string
    const getStr = (tag) => string(tag) || undefined;

    return {
        imagePixelModule: {
            pixelRepresentation: uint16('x00280103') || 0,
            bitsAllocated: uint16('x00280100') || 16,
            bitsStored: uint16('x00280101') || 12,
            highBit: uint16('x00280102') || 11,
            photometricInterpretation: getStr('x00280004') || 'MONOCHROME2',
            samplesPerPixel: uint16('x00280002') || 1,
            rows: uint16('x00280010'),
            columns: uint16('x00280011')
        },
        imagePlaneModule: {
            imageOrientationPatient: getFloatArray('x00200037'),
            imagePositionPatient: getFloatArray('x00200032'),
            pixelSpacing: getFloatArray('x00280030'),
            sliceThickness: parseFloat(getStr('x00180050')) || 1,
            frameOfReferenceUID: getStr('x00200052'),
            rows: uint16('x00280010'),
            columns: uint16('x00280011')
        },
        modality: {
            modality: getStr('x00080060') || 'CT', // Fallback to CT if missing, but try to read it
            seriesInstanceUID: getStr('x0020000e'),
        },
        series: {
             modality: getStr('x00080060') || 'CT',
        },
        generalSeriesModule: {
             modality: getStr('x00080060') || 'CT',
        },
        voiLutModule: {
            windowCenter: getFloatArray('x00281050'),
            windowWidth: getFloatArray('x00281051')
        },
        sopCommonModule: {
            sopInstanceUID: getStr('x00080018'),
            sopClassUID: getStr('x00080016'),
        }
    };
}
