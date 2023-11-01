import * as React from 'react';

export interface IconProps {
  name: string;
  className?: string;
  title?: string;
  svg_path?: string;
}

/**
 * Provide a `title` as an accessible label intended for screen readers.
 */
const Icon: React.FunctionComponent<IconProps> = ({
  name,
  className,
  title,
  svg_path,
}) => {
  if (name && svg_path) {
    return (
      <>
        <svg
          className={`icon icon-${name} ${className || ''}`}
          aria-hidden="true"
        >
          <path d={svg_path} />
        </svg>
        {title && <span className="visuallyhidden">{title}</span>}
      </>
    );
  }

  if (name) {
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
  }

  return null;
};

export default Icon;
