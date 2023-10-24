import * as React from 'react';

export interface IconProps {
  name: string;
  className?: string;
  title?: string;
}

/**
 * Provide a `title` as an accessible label intended for screen readers.
 */
const Icon: React.FunctionComponent<IconProps> = ({
  name,
  className,
  title,
}) => {
  if (name && name.startsWith('M')) {
    return (
      <svg className={`icon ${className || ''}`} aria-hidden="true">
        <path d={name} />
      </svg>
    );
  }

  return (
    <>
      <svg
        className={`icon icon-${name} ${className || ''}`}
        aria-hidden="true"
      >
        <use href={`#icon-${name}`} />
      </svg>
      {title && <span className="visuallyhidden">{title}</span>}
    </>
  );
};

export default Icon;
