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

  it('#className', () => {
    expect(shallow(<Icon name="test" className="u-test" />)).toMatchSnapshot();
  });

  it('#title', () => {
    expect(shallow(<Icon name="test" title="Test title" />)).toMatchSnapshot();
  });
});
