/* eslint-disable react/prop-types */

import React from 'react';

const handleClick = (
  href: string,
  onClick: ((e: React.MouseEvent) => void) | undefined,
  preventDefault: boolean,
  navigate: (url: string) => Promise<void>,
  e: React.MouseEvent
) => {
  if (preventDefault && href === '#' || navigate) {
    e.preventDefault();
    e.stopPropagation();
  }

  if (onClick) {
    onClick(e);
  } else if (navigate) {
    navigate(href);
  }
};

interface ButtonProps {
  className?: string;
  accessibleLabel?: string;
  href?: string;
  target?: string;
  preventDefault?: boolean;
  onClick?(e: React.MouseEvent): void;
  dialogTrigger?: boolean;
  navigate?(url: string): Promise<void>;
}

/**
 * A reusable button. Uses a <a> tag underneath.
 */
const Button: React.FunctionComponent<ButtonProps> = ({
  className = '',
  children,
  accessibleLabel,
  href = '#',
  target,
  preventDefault = true,
  onClick,
  dialogTrigger,
  navigate,
}) => {
  const hasText = children !== null;
  const accessibleElt = accessibleLabel ? (
    <span className="visuallyhidden">
      {accessibleLabel}
    </span>
  ) : null;

  return (
    <a
      className={className}
      onClick={handleClick.bind(null, href, onClick, preventDefault, navigate)}
      rel={target === '_blank' ? 'noopener noreferrer' : undefined}
      href={href}
      target={target}
      aria-haspopup={dialogTrigger ? 'dialog' : undefined}
    >
      {hasText ? children : accessibleElt}
    </a>
  );
};

export default Button;
