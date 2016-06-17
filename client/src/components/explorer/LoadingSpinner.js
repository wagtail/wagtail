import React from 'react';
import { STRINGS } from 'config';

const LoadingSpinner = () => (
  <div className="c-explorer__loading">
    <span className="c-explorer__spinner icon icon-spinner" /> {STRINGS['LOADING']}...
  </div>
);

export default LoadingSpinner;
