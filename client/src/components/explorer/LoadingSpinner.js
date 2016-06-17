import React from 'react';
import { STRINGS } from '../../config/wagtail';
import Icon from '../../components/Icon/Icon';

const LoadingSpinner = () => (
  <div className="c-explorer__loading">
    <Icon name="spinner" className="c-explorer__spinner" /> {STRINGS.LOADING}
  </div>
);

export default LoadingSpinner;
