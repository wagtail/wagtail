import React from 'react';

import { gettext } from '../../utils/gettext';
import Icon from '../Icon/Icon';

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
