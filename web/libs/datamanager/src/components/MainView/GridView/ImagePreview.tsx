import {
  useState,
  useRef,
  useEffect,
  type CSSProperties,
  useCallback,
} from "react";
import { observer } from "mobx-react";
import styles from "./GridPreview.module.scss";
import { cn } from "@synapse/ui";

const MAX_ZOOM = 20;
const ZOOM_FACTOR = 0.01;

type Task = {
  id: number;
  data: Record<string, string>;
};

type ImagePreviewProps = {
  task: Task;
  field: string;
};

/**
 * Secure the canvas element to prevent data extraction
 */
const secureCanvas = (canvas: HTMLCanvasElement) => {
  // Override toDataURL to prevent image extraction
  canvas.toDataURL = () => {
    console.warn("Image export is disabled for security reasons");
    return "";
  };

  // Override toBlob to prevent image extraction
  canvas.toBlob = () => {
    console.warn("Image export is disabled for security reasons");
  };

  // Prevent getImageData on the canvas context
  const ctx = canvas.getContext("2d");
  if (ctx) {
    const originalGetImageData = ctx.getImageData.bind(ctx);
    ctx.getImageData = (...args: Parameters<typeof originalGetImageData>) => {
      console.warn("Image data extraction is disabled for security reasons");
      // Return empty image data
      return new ImageData(1, 1);
    };
  }
};

// @todo constrain the position of the image to the container
const ImagePreview = observer(({ task, field }: ImagePreviewProps) => {
  const src = task.data?.[field] ?? "";

  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);

  const [imageLoaded, setImageLoaded] = useState(false);
  // visible container size
  const [containerSize, setContainerSize] = useState({ width: 0, height: 0 });
  // scaled image size
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 });

  // Zoom and position state
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });

  const [isDragging, setIsDragging] = useState(false);

  const dragParams = useRef({
    dragAnchor: { x: 0, y: 0 },
    startOffset: { x: 0, y: 0 },
  });

  // Reset on task change
  // biome-ignore lint/correctness/useExhaustiveDependencies: those are setStates, not values
  useEffect(() => {
    setScale(1);
    setIsDragging(false);
    setImageLoaded(false);
  }, [task, src]);

  // Load image and render to canvas
  useEffect(() => {
    if (!src || !containerRef.current) return;

    const img = new Image();
    img.crossOrigin = "anonymous";
    imageRef.current = img;

    img.onload = () => {
      if (!containerRef.current || !canvasRef.current) return;

      const containerRect = containerRef.current.getBoundingClientRect();

      setContainerSize({
        width: containerRect.width,
        height: containerRect.height,
      });

      const coverScaleX = containerRect.width / img.naturalWidth;
      const coverScaleY = containerRect.height / img.naturalHeight;
      const imageScale = Math.min(coverScaleX, coverScaleY);

      const scaledWidth = img.naturalWidth * imageScale;
      const scaledHeight = img.naturalHeight * imageScale;

      setImageSize({
        width: scaledWidth,
        height: scaledHeight,
      });

      // Center the image initially
      const initialX = (containerRect.width - scaledWidth) / 2;
      const initialY = (containerRect.height - scaledHeight) / 2;

      setOffset({ x: initialX, y: initialY });

      // Set canvas size and render image
      const canvas = canvasRef.current;
      canvas.width = containerRect.width;
      canvas.height = containerRect.height;

      const ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, initialX, initialY, scaledWidth, scaledHeight);
      }

      // Secure the canvas after initial render
      secureCanvas(canvas);
      setImageLoaded(true);
    };

    img.onerror = () => {
      console.error("Failed to load image:", src);
    };

    img.src = src;

    return () => {
      img.onload = null;
      img.onerror = null;
    };
  }, [src]);

  // Re-render canvas when zoom/offset changes
  useEffect(() => {
    if (
      !imageLoaded ||
      !canvasRef.current ||
      !imageRef.current ||
      !containerRef.current
    )
      return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const img = imageRef.current;

    if (!ctx) return;

    const containerRect = containerRef.current.getBoundingClientRect();
    canvas.width = containerRect.width;
    canvas.height = containerRect.height;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const scaledWidth = imageSize.width * scale;
    const scaledHeight = imageSize.height * scale;

    ctx.drawImage(img, offset.x, offset.y, scaledWidth, scaledHeight);

    // Re-secure the canvas after each render
    secureCanvas(canvas);
  }, [imageLoaded, scale, offset, imageSize]);

  const constrainOffset = useCallback(
    (newOffset: { x: number; y: number }) => {
      const { x, y } = newOffset;
      const { width, height } = imageSize;
      const { width: containerWidth, height: containerHeight } = containerSize;

      // to preserve paddings and make it less weird
      const minX = (containerWidth - width) / 2;
      const minY = (containerHeight - height) / 2;
      // the far edges should be behind container edges
      const maxX = Math.max(width * scale - containerWidth, 0);
      const maxY = Math.max(height * scale - containerHeight, 0);

      return {
        x: Math.min(Math.max(x, -maxX), minX),
        y: Math.min(Math.max(y, -maxY), minY),
      };
    },
    [imageSize, containerSize, scale]
  );

  const handleWheel = useCallback(
    (e: React.WheelEvent) => {
      if (!containerRef.current || !imageLoaded) return;

      const container = containerRef.current;
      const rect = container.getBoundingClientRect();

      // Calculate cursor position relative to center
      const cursorX = e.clientX - rect.left;
      const cursorY = e.clientY - rect.top;

      // Zoom calculation
      const newScale =
        e.deltaY < 0
          ? Math.min(scale * (1 + ZOOM_FACTOR), MAX_ZOOM) // Max zoom
          : Math.max(scale * (1 - ZOOM_FACTOR), 1); // Min zoom

      // Calculate zoom translation
      const scaleDelta = newScale / scale;
      const newX = cursorX - (cursorX - offset.x) * scaleDelta;
      const newY = cursorY - (cursorY - offset.y) * scaleDelta;

      setScale(newScale);
      setOffset(constrainOffset({ x: newX, y: newY }));
    },
    [imageLoaded, offset, scale, constrainOffset]
  );

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!containerRef.current) return;

      const { x: oldX, y: oldY } = dragParams.current.dragAnchor;
      const { x: offsetX, y: offsetY } = dragParams.current.startOffset;
      const newX = e.clientX - oldX;
      const newY = e.clientY - oldY;

      setOffset(constrainOffset({ x: offsetX + newX, y: offsetY + newY }));
    },
    [constrainOffset]
  );

  const handleMouseUp = useCallback(
    (e: MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();

      setIsDragging(false);

      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    },
    [handleMouseMove]
  );

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (!containerRef.current || scale <= 1) return;

      setIsDragging(true);
      dragParams.current.dragAnchor = { x: e.clientX, y: e.clientY };
      dragParams.current.startOffset = { ...offset };

      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("click", handleMouseUp, {
        capture: true,
        once: true,
      });
    },
    [scale, offset, handleMouseMove, handleMouseUp]
  );

  // Security: Prevent right-click context menu
  const handleContextMenu = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    return false;
  }, []);

  // Security: Prevent drag operations
  const handleDragStart = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    return false;
  }, []);

  // Container styles
  const containerStyle: CSSProperties = {
    minHeight: "200px",
    maxHeight: "calc(90vh - 120px)",
    width: "100%",
    position: "relative",
    overflow: "hidden",
    cursor: scale > 1 ? (isDragging ? "grabbing" : "grab") : "default",
    userSelect: "none",
    WebkitUserSelect: "none",
  };

  // Canvas styles
  const canvasStyle: CSSProperties = {
    width: "100%",
    height: "100%",
    display: "block",
    pointerEvents: "none", // Let container handle events
  };

  return (
    <div
      ref={containerRef}
      style={containerStyle}
      className={cn(styles.imageContainer, "px-tight")}
      onWheel={handleWheel}
      onMouseDown={handleMouseDown}
      onContextMenu={handleContextMenu}
      onDragStart={handleDragStart}
    >
      {src && (
        <canvas ref={canvasRef} style={canvasStyle} className={styles.image} />
      )}
      {!imageLoaded && src && (
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            color: "var(--text-secondary)",
          }}
        >
          Loading...
        </div>
      )}
    </div>
  );
});

const ImagePreviewWrapper = observer(({ task, field }: ImagePreviewProps) => {
  if (!task || !field) return null;
  return <ImagePreview task={task} field={field} />;
});

export { ImagePreviewWrapper as ImagePreview };
