import React from 'react';
import { shallow } from 'enzyme';

import Tooltip from './Tooltip';

const target = {
  top: 1,
  left: 1,
  width: 12,
  height: 1200,
};

describe('Tooltip', () => {
  it('#direction top', () => {
    expect(
      shallow(
        <Tooltip target={target} direction="top">
          Test
        </Tooltip>,
      ),
    ).toMatchSnapshot();
  });

  it('#direction left', () => {
    expect(
      shallow(
        <Tooltip target={target} direction="left">
          Test
        </Tooltip>,
      ),
    ).toMatchSnapshot();
  });

  it('#direction top-left', () => {
    expect(
      shallow(
        <Tooltip target={target} direction="top-left">
          Test
        </Tooltip>,
      ),
    ).toMatchSnapshot();
  });
});
