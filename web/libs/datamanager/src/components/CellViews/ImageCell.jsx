import { getRoot } from "mobx-state-tree";
import { AnnotationPreview } from "../Common/AnnotationPreview/AnnotationPreview";
import { SecureImage } from "../Common/SecureImage";

export const ImageCell = (column) => {
  const {
    original,
    value,
    column: { alias },
  } = column;
  const root = getRoot(original);

  // DEBUG: Log what ImageCell receives
  console.log("[ImageCell] Render:", {
    taskId: original?.id,
    value,
    valueType: typeof value,
    isArray: Array.isArray(value),
    alias,
    dataKeys:
      original?.data instanceof Map
        ? Array.from(original.data.keys())
        : "not a map",
    dataImage: original?.data?.get?.("image") || original?.data?.image,
  });

  const renderImagePreview =
    original.total_annotations === 0 || !root.showPreviews;
  const imgSrc = Array.isArray(value) ? value[0] : value;

  console.log("[ImageCell] After processing:", {
    taskId: original?.id,
    imgSrc,
    renderImagePreview,
    fullURL: imgSrc ? `${window.location.origin}${imgSrc}` : "NO SRC",
  });

  if (!imgSrc) return null;

  return renderImagePreview ? (
    <SecureImage
      key={imgSrc}
      src={imgSrc}
      alt="Data"
      style={{
        maxHeight: "100%",
        maxWidth: "100px",
        objectFit: "contain",
        borderRadius: 3,
      }}
    />
  ) : (
    <AnnotationPreview
      task={original}
      annotation={original.annotations[0]}
      config={getRoot(original).SDK}
      name={alias}
      variant="120x120"
      fallbackImage={value}
      style={{
        maxHeight: "100%",
        maxWidth: "100px",
        objectFit: "contain",
        borderRadius: 3,
      }}
    />
  );
};
