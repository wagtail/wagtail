import PropTypes from 'prop-types';
import React from 'react';

/**
 * Abstracts away the actual icon implementation (font icons, SVG icons, CSS sprite).
 * Provide a `title` as an accessible label intended for screen readers.
 */
const Icon = ({ name, className, title }) => (
  <span>
    <span className={`icon icon-${name} ${className || ''}`} aria-hidden></span>
    {title ? (
      <span className="visuallyhidden">
        {title}
      </span>
    ) : null}
  </span>
);

Icon.propTypes = {
  name: PropTypes.string.isRequired,
  className: PropTypes.string,
  title: PropTypes.string,
};

Icon.defaultProps = {
  className: null,
  title: null,
};

export default Icon;
