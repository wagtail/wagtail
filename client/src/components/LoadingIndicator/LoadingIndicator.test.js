import React from 'react';
import { shallow } from 'enzyme';

import LoadingIndicator from './LoadingIndicator';

describe('LoadingIndicator', () => {
  it('exists', () => {
    expect(LoadingIndicator).toBeDefined();
  });

  it('basic', () => {
    expect(shallow(<LoadingIndicator />)).toMatchSnapshot();
  });
});
