import React from 'react';
import PropTypes from 'prop-types';

const propTypes = {
  isActive: PropTypes.bool,
  children: PropTypes.node,
};

const defaultProps = {
  isActive: false,
  children: null,
};

const ModalSpinner = ({ isActive, children }) =>
  <div className={`loading-mask${isActive ? ' loading' : ''}`}>
    {children}
  </div>;

ModalSpinner.propTypes = propTypes;
ModalSpinner.defaultProps = defaultProps;

export default ModalSpinner;
