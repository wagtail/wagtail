import React from 'react';
import { shallow } from 'enzyme';

import Transition, { PUSH } from './Transition';

describe('Transition', () => {
  it('exists', () => {
    expect(Transition).toBeDefined();
  });

  it('basic', () => {
    expect(shallow(<Transition name={PUSH} />)).toMatchSnapshot();
  });
});
