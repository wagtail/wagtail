import React from 'react';
import { shallow } from 'enzyme';

import LoadingSpinner from './LoadingSpinner';

describe('LoadingSpinner', () => {
  it('exists', () => {
    expect(LoadingSpinner).toBeDefined();
  });

  it('basic', () => {
    expect(shallow(<LoadingSpinner />)).toMatchSnapshot();
  });
});
