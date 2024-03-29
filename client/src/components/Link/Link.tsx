import * as React from 'react';

const handleClick = (
  href: string,
  onClick: ((e: React.MouseEvent) => void) | undefined,
  preventDefault: boolean,
  navigate: (url: string) => Promise<void>,
  e: React.MouseEvent,
) => {
  if (preventDefault && href === '#') {
    e.preventDefault();
    e.stopPropagation();
  }

  if (onClick) {
    onClick(e);
  }

  // Do not capture click events with modifier keys or non-main buttons.
  if (e.ctrlKey || e.shiftKey || e.metaKey || (e.button && e.button !== 0)) {
    return;
  }

  // If a navigate handler has been specified, replace the default behaviour
  if (navigate && !e.defaultPrevented) {
    e.preventDefault();
    navigate(href);
  }
};

interface LinkProps {
  className?: string;
  accessibleLabel?: string;
  href?: string;
  target?: string;
  preventDefault?: boolean;
  onClick?(e: React.MouseEvent): void;
  navigate?(url: string): Promise<void>;
}

/**
 * A reusable button. Uses a <a> tag underneath.
 */
const Link: React.FunctionComponent<LinkProps> = ({
  className = '',
  children,
  accessibleLabel,
  href = '#',
  target,
  preventDefault = true,
  onClick,
  navigate,
}) => {
  const hasText = React.Children.count(children) > 0;
  const accessibleElt = accessibleLabel ? (
    <span className="w-sr-only">{accessibleLabel}</span>
  ) : null;

  return (
    <a
      className={className}
      onClick={handleClick.bind(null, href, onClick, preventDefault, navigate)}
      rel={target === '_blank' ? 'noreferrer' : undefined}
      href={href}
      target={target}
    >
      {hasText ? children : accessibleElt}
    </a>
  );
};

export default Link;
