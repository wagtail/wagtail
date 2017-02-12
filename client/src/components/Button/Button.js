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
  href: React.PropTypes.string,
  className: React.PropTypes.string,
  icon: React.PropTypes.oneOfType([
    React.PropTypes.string,
    React.PropTypes.arrayOf(React.PropTypes.string),
  ]),
  target: React.PropTypes.string,
  children: React.PropTypes.node,
  accessibleLabel: React.PropTypes.string,
  onClick: React.PropTypes.func,
  isLoading: React.PropTypes.bool,
  preventDefault: React.PropTypes.bool,
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
