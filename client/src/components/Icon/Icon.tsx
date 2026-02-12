import * as React from 'react';

export interface IconProps extends React.SVGProps<SVGSVGElement> {
  /** Optional svg `path` instead of the `use` based on the icon name. */
  children?: React.ReactNode;
  className?: string;
  name: string;
  title?: string;
}

/**
 * Provide a `title` as an accessible label intended for screen readers.
 */
const Icon: React.FunctionComponent<IconProps> = ({
  children,
  className,
  name,
  title,
  ...props
}) => (
  <>
    <svg
      {...props}
      className={['icon', `icon-${name}`, className || '']
        .filter(Boolean)
        .join(' ')}
      aria-hidden="true"
    >
      {children || <use href={`#icon-${name}`} />}
    </svg>
    {title && <span className="w-sr-only">{title}</span>}
  </>
);

export default Icon;
