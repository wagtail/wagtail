import React from 'react';
import { shallow } from 'enzyme';

import Button from './Button';

describe('Button', () => {
  it('exists', () => {
    expect(Button).toBeDefined();
  });

  it('basic', () => {
    expect(shallow(<Button />)).toMatchSnapshot();
  });

  it('#children', () => {
    expect(shallow(<Button>To infinity and beyond!</Button>)).toMatchSnapshot();
  });

  it('#accessibleLabel', () => {
    expect(shallow(<Button accessibleLabel="I am here in the shadows" />)).toMatchSnapshot();
  });

  it('#icon', () => {
    expect(shallow(<Button icon="test-icon" />)).toMatchSnapshot();
  });

  it('#target', () => {
    expect(shallow(<Button target="_blank" />)).toMatchSnapshot();
  });

  it('#multiple icons', () => {
    expect(shallow(<Button icon={['test-icon', 'secondary-icon']} />)).toMatchSnapshot();
  });

  it('#icon changes with #isLoading', () => {
    expect(shallow(<Button icon="test-icon" isLoading={true} />)).toMatchSnapshot();
  });

  it('is clickable', () => {
    const onClick = jest.fn();
    shallow(<Button onClick={onClick} />).simulate('click', {
      preventDefault() {},
      stopPropagation() {},
    });
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('dismisses clicks', () => {
    const preventDefault = jest.fn();
    shallow(<Button />).simulate('click', {
      preventDefault,
      stopPropagation() {},
    });
    expect(preventDefault).toHaveBeenCalledTimes(1);
  });
});
