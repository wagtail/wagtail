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

const PageChooserSpinner = ({ isActive, children }) =>
  <div className={`loading-mask${isActive ? ' loading' : ''}`}>
    {children}
  </div>;

PageChooserSpinner.propTypes = propTypes;
PageChooserSpinner.defaultProps = defaultProps;

export default PageChooserSpinner;
