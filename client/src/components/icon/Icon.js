import React, { PropTypes } from 'react';

const Icon = ({ name, className, title }) => (
  <span className={`icon icon-${name} ${className}`} aria-hidden={!title}>
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
  title: PropTypes.string,
};

Icon.defaultProps = {
  className: '',
  title: null,
};

export default Icon;
