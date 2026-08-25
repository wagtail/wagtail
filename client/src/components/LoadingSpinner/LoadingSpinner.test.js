import { shallow } from 'enzyme';
import React from 'react';

import LoadingSpinner from './LoadingSpinner';

describe('LoadingSpinner', () => {
  it('exists', () => {
    expect(LoadingSpinner).toBeDefined();
  });

  it('basic', () => {
    expect(shallow(<LoadingSpinner />)).toMatchSnapshot();
  });
});
