import React from "react";
import "./ExpertiseDropdown.scss";

/**
 * ExpertiseDropdown - Reusable dropdown component for expertise selection
 * Follows Lambda Design System patterns
 */

export interface DropdownOption {
  id: number;
  name: string;
  icon?: string;
}

export interface ExpertiseDropdownProps {
  label: string;
  value: number | null;
  options: DropdownOption[];
  placeholder?: string;
  onChange: (value: number | null) => void;
  disabled?: boolean;
  loading?: boolean;
}

export const ExpertiseDropdown: React.FC<ExpertiseDropdownProps> = ({
  label,
  value,
  options,
  placeholder = "Select...",
  onChange,
  disabled = false,
  loading = false,
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedValue = e.target.value;
    onChange(selectedValue ? parseInt(selectedValue, 10) : null);
  };

  return (
    <div className="expertise-dropdown">
      <label className="expertise-dropdown__label">{label}</label>
      <div className="expertise-dropdown__wrapper">
        <select
          className="expertise-dropdown__select"
          value={value ?? ""}
          onChange={handleChange}
          disabled={disabled || loading}
        >
          <option value="">{loading ? "Loading..." : placeholder}</option>
          {options.map((option) => (
            <option key={option.id} value={option.id}>
              {option.name}
            </option>
          ))}
        </select>
        
      </div>
    </div>
  );
};

export default ExpertiseDropdown;
