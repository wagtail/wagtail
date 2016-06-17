import React from 'react';
import { STRINGS } from '../../config/wagtail';

const LoadingIndicator = () => (
  <div className="o-icon c-indicator is-spinning">
    <span ariaRole="presentation">{STRINGS.LOADING}</span>
  </div>
);

export default LoadingIndicator;
