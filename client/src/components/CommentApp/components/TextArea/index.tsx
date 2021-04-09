/* eslint-disable react/prop-types */

import React, { FunctionComponent } from 'react';

export interface TextAreaProps {
  value: string;
  className?: string;
  placeholder?: string;
  onChange?(newValue: string): void;
  focusOnMount?: boolean;
}

const TextArea: FunctionComponent<TextAreaProps> = ({
  value,
  className,
  placeholder,
  onChange,
  focusOnMount
}) => {
  const onChangeValue = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    if (onChange) {
      onChange(e.target.value);
    }
  };

  // Resize the textarea whenever the value is changed
  const textAreaElement = React.useRef<HTMLTextAreaElement>(null);
  React.useEffect(() => {
    if (textAreaElement.current) {
      textAreaElement.current.style.height = '';
      textAreaElement.current.style.height =
        textAreaElement.current.scrollHeight + 'px';
    }
  }, [value, textAreaElement]);

  // Focus the textarea when it is mounted
  React.useEffect(() => {
    if (focusOnMount && textAreaElement.current) {
      textAreaElement.current.focus();
    }
  }, [textAreaElement]);

  return (
    <textarea
      rows={1}
      style={{ resize: 'none', overflowY: 'hidden' }}
      className={className}
      placeholder={placeholder}
      ref={textAreaElement}
      onChange={onChangeValue}
      value={value}
    />
  );
};

export default TextArea;
