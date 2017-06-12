import React from 'react';
import PropTypes from 'prop-types';

const propTypes = {
  errorMessage: PropTypes.node,
};

const defaultProps = {
  errorMessage: null,
};

const PageChooserErrorView = ({ errorMessage }) =>
  <div className="nice-padding">
    <div className="help-block help-critical">
      {errorMessage}
    </div>
  </div>;

PageChooserErrorView.propTypes = propTypes;
PageChooserErrorView.defaultProps = defaultProps;

export default PageChooserErrorView;
