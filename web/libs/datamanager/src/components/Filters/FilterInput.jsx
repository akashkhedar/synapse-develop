import React from "react";
import Input from "../Common/Input/Input";

export const FilterInput = ({ value, type, onChange, placeholder, schema, style }) => {
  const inputRef = React.useRef();
  const onChangeHandler = () => {
    const value = inputRef.current?.value ?? inputRef.current?.input?.value;

    onChange(value);
  };

  return (
    <Input
      rawClassName="h-full min-w-[100px]"
      size="small"
      type={type}
      value={value ?? ""}
      ref={inputRef}
      placeholder={placeholder}
      onChange={onChangeHandler}
      style={{
        ...style,
        fontFamily: "'Space Grotesk', system-ui, -apple-system, sans-serif",
        fontSize: '13px',
        fontWeight: 500,
        color: '#e5e7eb',
        background: 'rgba(139, 92, 246, 0.05)',
        border: '1px solid rgba(139, 92, 246, 0.2)',
        borderRadius: '6px',
        transition: 'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)',
      }}
      {...(schema ?? {})}
    />
  );
};

