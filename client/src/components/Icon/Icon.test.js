import React from 'react';
import { shallow } from 'enzyme';
import Icon from './Icon';

describe('Icon', () => {
  it('exists', () => {
    expect(Icon).toBeDefined();
  });

  it('#name', () => {
    expect(shallow(<Icon name="test" />)).toMatchSnapshot();
  });

  it('#name for SVG path data', () => {
    const svgPathData = 'M10 30 L20 10 L30 30 L40 30 L50 10 L60 30';
    expect(shallow(<Icon name={svgPathData} />)).toMatchSnapshot();
  });

  it('#className', () => {
    expect(shallow(<Icon name="test" className="u-test" />)).toMatchSnapshot();
  });

  it('#title', () => {
    expect(shallow(<Icon name="test" title="Test title" />)).toMatchSnapshot();
  });
});
