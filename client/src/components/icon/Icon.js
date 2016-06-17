import React, { PropTypes } from 'react';

// TODO Add support for accessible label.
const Icon = ({ name, className }) => (
  <span className={`icon icon-${name} ${className}`} />
);

Icon.propTypes = {
  name: PropTypes.string.isRequired,
  className: PropTypes.string,
};

Icon.defaultProps = {
  className: '',
};

export default Icon;
