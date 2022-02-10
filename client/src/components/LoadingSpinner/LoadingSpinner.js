import React from 'react';
import Icon from '../../components/Icon/Icon';

/**
 * A loading indicator with a text label next to it.
 */
const LoadingSpinner = () => (
  <span>
    <Icon name="spinner" className="c-spinner" />
    {` ${gettext('Loading…')}`}
  </span>
);

export default LoadingSpinner;
