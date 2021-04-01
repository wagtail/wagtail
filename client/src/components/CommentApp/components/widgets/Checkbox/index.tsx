import React from 'react';

export interface CheckboxProps {
  id: string;
  label: string;
  checked: boolean;
  disabled?: boolean;
  onChange?: (checked: boolean) => any;
}

const Checkbox = (props: CheckboxProps) => {
  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (props.onChange) {
      props.onChange(e.target.checked);
    }
  };

  if (props.disabled) {
    return (
      <div className="checkbox">
        <input
          id={props.id}
          type="checkbox"
          checked={props.checked}
          disabled={true}
        />
        <label htmlFor={props.id}>{props.label}</label>
      </div>
    );
  }
  return (
    <div className="checkbox">
      <input
        id={props.id}
        type="checkbox"
        onChange={onChange}
        checked={props.checked}
      />
      <label htmlFor={props.id}>{props.label}</label>
    </div>
  );
};

export default Checkbox;
