import React from 'react';
import { shallow } from 'enzyme';

import AbsoluteDate from './AbsoluteDate';

describe('AbsoluteDate', () => {
  it('exists', () => {
    expect(AbsoluteDate).toBeDefined();
  });

  it('basic', () => {
    expect(shallow(<AbsoluteDate />)).toMatchSnapshot();
  });

  it('#time', () => {
    expect(shallow(<AbsoluteDate time="2016-09-19T20:22:33.356623Z" />)).toMatchSnapshot();
  });
});
