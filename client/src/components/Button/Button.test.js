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

  it('#dialogTrigger', () => {
    expect(shallow(<Button dialogTrigger />)).toMatchSnapshot();
  });

  it('#target', () => {
    expect(shallow(<Button target="_blank" rel="noopener noreferrer" />)).toMatchSnapshot();
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
