import React from 'react';
import { STRINGS } from '../../config/wagtailConfig';
import Icon from '../../components/Icon/Icon';

/**
 * A loading indicator with a text label next to it.
 */
const LoadingSpinner = () => (
  <span>
    <Icon name="spinner" className="c-spinner" />{` ${STRINGS.LOADING}`}
  </span>
);

export default LoadingSpinner;
