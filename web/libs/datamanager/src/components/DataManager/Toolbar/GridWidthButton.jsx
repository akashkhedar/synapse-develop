import { inject } from "mobx-react";
import { useCallback, useState } from "react";
import { Button, ButtonGroup } from "@synapse/ui";
import { Dropdown } from "@synapse/ui";
import { Toggle } from "../../Common/Form";
import { IconSettings, IconMinus, IconPlus } from "@synapse/icons";
import debounce from "lodash/debounce";
import { cn } from "../../../utils/bem";
import "./TabPanel.scss";

const injector = inject(({ store }) => {
  const view = store?.currentView;

  const cols = view.fieldsAsColumns ?? [];
  const hasImage = cols.some(({ type }) => type === "Image") ?? false;

  return {
    view,
    isGrid: view.type === "grid",
    gridWidth: view?.gridWidth,
    fitImagesToWidth: view?.gridFitImagesToWidth,
    hasImage,
  };
});

export const GridWidthButton = injector(({ view, isGrid, gridWidth, fitImagesToWidth, hasImage, size }) => {
  const [width, setWidth] = useState(gridWidth);
  const [isHovered, setIsHovered] = useState(false);

  const setGridWidthStore = debounce((value) => {
    view.setGridWidth(value);
  }, 200);

  const setGridWidth = useCallback(
    (width) => {
      const newWidth = Math.max(1, Math.min(width, 10));

      setWidth(newWidth);
      setGridWidthStore(newWidth);
    },
    [view],
  );

  const handleFitImagesToWidthToggle = useCallback(
    (e) => {
      view.setFitImagesToWidth(e.target.checked);
    },
    [view],
  );



  return isGrid ? (
    <Dropdown.Trigger
      content={
        <div className="p-tight min-w-wide space-y-base">
          <div className="grid grid-cols-[1fr_min-content] gap-base items-center">
            <span>Columns: {width}</span>
            <ButtonGroup collapsed={false}>
              <Button
                onClick={() => setGridWidth(width - 1)}
                disabled={width === 1}
                variant="neutral"
                look="outlined"
                leading={<IconMinus />}
                size="small"
                aria-label="Decrease columns number"
              />
              <Button
                onClick={() => setGridWidth(width + 1)}
                disabled={width === 10}
                variant="neutral"
                look="outlined"
                leading={<IconPlus />}
                size="small"
                aria-label="Increase columns number"
              />
            </ButtonGroup>
          </div>
          {hasImage && (
            <div className="grid grid-cols-[1fr_min-content] gap-base items-center">
              <span>Fit images to width</span>
              <Toggle checked={fitImagesToWidth} onChange={handleFitImagesToWidthToggle} />
            </div>
          )}
        </div>
      }
    >

      <button 
          aria-label="Grid settings" 
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          style={{
            background: 'black',
            border: `1px solid ${isHovered ? 'rgba(139, 92, 246, 0.5)' : 'rgba(55, 65, 81, 0.5)'}`,
            borderRadius: '10px',
            color: '#c4b5fd',
            fontWeight: 600,
            fontSize: '13px',
            height: '32px',
            padding: '0 14px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: "'Space Grotesk', system-ui, -apple-system, sans-serif",
            outline: 'none',
            transition: 'all 0.15s ease',
            boxShadow: isHovered ? '0 0 12px rgba(139, 92, 246, 0.15)' : 'none',
          }}
      >
        <IconSettings style={{ width: 16, height: 16 }} />
      </button>
    </Dropdown.Trigger>
  ) : null;
});

