import PropTypes from 'prop-types';
import React from 'react';

const getClassName = (className, icon) => {
  const hasIcon = icon !== '';
  let iconName = '';
  if (hasIcon) {
    if (typeof icon === 'string') {
      iconName = ` icon-${icon}`;
    } else {
      iconName = icon.map(val => ` icon-${val}`).join('');
    }
  }
  return `${className} ${hasIcon ? 'icon' : ''}${iconName}`;
};

const handleClick = (href, onClick, preventDefault, e) => {
  if (preventDefault && href === '#') {
    e.preventDefault();
    e.stopPropagation();
  }

  if (onClick) {
    onClick(e);
  }
};

/**
 * A reusable button. Uses a <a> tag underneath.
 */
const Button = ({
  className,
  icon,
  children,
  accessibleLabel,
  isLoading,
  href,
  target,
  preventDefault,
  onClick,
}) => {
  const hasText = children !== null;
  const iconName = isLoading ? 'spinner' : icon;
  const accessibleElt = accessibleLabel ? (
    <span className="visuallyhidden">
      {accessibleLabel}
    </span>
  ) : null;

  return (
    <a
      className={getClassName(className, iconName)}
      onClick={handleClick.bind(null, href, onClick, preventDefault)}
      rel={target === '_blank' ? 'noopener noreferrer' : null}
      href={href}
      target={target}
    >
      {hasText ? children : accessibleElt}
    </a>
  );
};

Button.propTypes = {
  href: PropTypes.string,
  className: PropTypes.string,
  icon: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.arrayOf(PropTypes.string),
  ]),
  target: PropTypes.string,
  children: PropTypes.node,
  accessibleLabel: PropTypes.string,
  onClick: PropTypes.func,
  isLoading: PropTypes.bool,
  preventDefault: PropTypes.bool,
};

Button.defaultProps = {
  href: '#',
  className: '',
  icon: '',
  target: null,
  children: null,
  accessibleLabel: null,
  onClick: null,
  isLoading: false,
  preventDefault: true,
};

export default Button;
