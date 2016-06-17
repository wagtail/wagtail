import React, { PropTypes } from 'react';

const Icon = ({ name, className, title }) => (
  <span className={`icon icon-${name} ${className}`}>
    {title ? (
        <span aria-role="presentation">
            {title}
        </span>
    ) : null}
  </span>
);

Icon.propTypes = {
  name: PropTypes.string.isRequired,
  className: PropTypes.string,
};

Icon.defaultProps = {
  className: '',
};

export default Icon;
