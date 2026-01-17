import { inject, observer } from "mobx-react";
import { useEffect, useState } from "react";
// @ts-ignore - RadioGroup is a .jsx file without types
import { RadioGroup } from "../../Common/RadioGroup/RadioGroup";
import { IconRows3, IconRows4 } from "@synapse/icons";
import { Tooltip } from "@synapse/ui";

// Density constants - exported for use in other components
export const DENSITY_STORAGE_KEY = "dm:table:density";
export const DENSITY_COMFORTABLE = "comfortable" as const;
export const DENSITY_COMPACT = "compact" as const;

// Row height values for each density
export const ROW_HEIGHT_COMFORTABLE = 70;
export const ROW_HEIGHT_COMPACT = 50;

export type Density = typeof DENSITY_COMFORTABLE | typeof DENSITY_COMPACT;

interface DensityToggleProps {
  size?: "small" | "medium" | "large";
  onChange?: (density: Density) => void;
  storageKey?: string;
  view?: { type: string };
}

const densityInjector = inject(({ store }: any) => ({
  view: store.currentView,
}));

export const DensityToggle = densityInjector(
  observer(({ size, onChange, storageKey, view, ...rest }: DensityToggleProps) => {
    const key = storageKey ?? DENSITY_STORAGE_KEY;
    const [density, setDensity] = useState<Density>(() => {
      return (localStorage.getItem(key) as Density) ?? DENSITY_COMFORTABLE;
    });

    useEffect(() => {
      localStorage.setItem(key, density);
      onChange?.(density);

      // Notify other components about density change
      window.dispatchEvent(new CustomEvent("dm:density:changed", { detail: density }));
    }, [density, onChange, key]);

    // Hide density toggle when in grid view
    if (view?.type === "grid") {
      return null;
    }

    // Modern toggle container style
    const toggleContainerStyle = {
      display: 'flex',
      gap: '2px',
      background: 'black',
      border: '1px solid rgba(55, 65, 81, 0.5)',
      borderRadius: '10px',
      padding: '3px',
      height: '32px',
      alignItems: 'center',
    };

    const buttonStyle = {
      background: 'transparent',
      border: 'none',
      borderRadius: '7px',
      color: '#c4b5fd',
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '26px',
      width: '26px',
      padding: '0',
    };

    const buttonActiveStyle = {
      ...buttonStyle,
      background: 'rgba(139, 92, 246, 0.2)',
    };

    return (
      <RadioGroup
        size={size}
        value={density}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setDensity(e.target.value as Density)}
        {...rest}
        style={toggleContainerStyle as React.CSSProperties}
        data-testid="density-toggle"
      >
        <Tooltip title="Comfortable density">
          <div>
            <RadioGroup.Button
              value={DENSITY_COMFORTABLE}
              aria-label="Comfortable density"
              data-testid="density-comfortable"
              style={density === DENSITY_COMFORTABLE ? buttonActiveStyle : buttonStyle}
            >
              <IconRows3 style={{ width: 16, height: 16 }} />
            </RadioGroup.Button>
          </div>
        </Tooltip>
        <Tooltip title="Compact density">
          <div>
            <RadioGroup.Button 
              value={DENSITY_COMPACT} 
              aria-label="Compact density" 
              data-testid="density-compact"
              style={density === DENSITY_COMPACT ? buttonActiveStyle : buttonStyle}
            >
              <IconRows4 style={{ width: 16, height: 16 }} />
            </RadioGroup.Button>
          </div>
        </Tooltip>
      </RadioGroup>
    );
  }),
);

