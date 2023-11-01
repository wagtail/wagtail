import * as React from 'react';

export interface IconProps {
  name: string;
  className?: string;
  title?: string;
  svgPath?: string;
}

/**
 * Provide a `title` as an accessible label intended for screen readers.
 */
const Icon: React.FunctionComponent<IconProps> = ({
  name,
  className,
  title,
  svgPath,
}) => {
  if (name && svgPath) {
    return (
      <>
        <svg
          className={`icon icon-${name} ${className || ''}`}
          aria-hidden="true"
        >
          <path d={svgPath} />
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
