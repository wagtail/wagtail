import { shallow } from 'enzyme';
import React from 'react';

import Transition, { PUSH } from './Transition';

describe('Transition', () => {
  it('exists', () => {
    expect(Transition).toBeDefined();
  });

  it('basic', () => {
    expect(shallow(<Transition name={PUSH} />)).toMatchSnapshot();
  });

  it('label', () => {
    expect(
      shallow(<Transition name={PUSH} label="Page explorer" />),
    ).toMatchSnapshot();
  });
});
