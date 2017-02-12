import React from 'react';

/**
 * Abstracts away the actual icon implementation (font icons, SVG icons, CSS sprite).
 * Provide a `title` as an accessible label intended for screen readers.
 */
const Icon = ({ name, className, title }) => (
  <span>
    <span className={`icon icon-${name} ${className}`} aria-hidden></span>
    {title ? (
      <span className="visuallyhidden">
        {title}
      </span>
    ) : null}
  </span>
);

Icon.propTypes = {
  name: React.PropTypes.string.isRequired,
  className: React.PropTypes.string,
  title: React.PropTypes.string,
};

Icon.defaultProps = {
  className: '',
  title: null,
};

export default Icon;
