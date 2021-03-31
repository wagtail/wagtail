import React from 'react';

export interface RadioProps {
  id: string;
  name: string;
  value: string;
  label: string;
  checked: boolean;
  disabled?: boolean;
  onChange?: (value: string) => any;
}

const Radio = (props: RadioProps) => {
  const onChange = () => {
    if (props.onChange) {
      props.onChange(props.value);
    }
  };

  if (props.disabled) {
    return (
      <div className="radio">
        <input
          id={props.id}
          type="radio"
          name={props.name}
          checked={props.checked}
          disabled={true}
        />
        <label htmlFor={props.id}>{props.label}</label>
      </div>
    );
  }
  return (
    <div className="radio">
      <input
        id={props.id}
        type="radio"
        name={props.name}
        onChange={onChange}
        checked={props.checked}
      />
      <label htmlFor={props.id}>{props.label}</label>
    </div>
  );
};

export default Radio;
