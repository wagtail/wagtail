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
    expect(
      shallow(<Button accessibleLabel="I am here in the shadows" />),
    ).toMatchSnapshot();
  });

  it('#dialogTrigger', () => {
    expect(shallow(<Button dialogTrigger />)).toMatchSnapshot();
  });

  it('#target', () => {
    expect(
      shallow(<Button target="_blank" rel="noreferrer" />),
    ).toMatchSnapshot();
  });

  it('is clickable', () => {
    const onClick = jest.fn();
    shallow(<Button onClick={onClick} />).simulate('click', {
      preventDefault: jest.fn(),
      stopPropagation: jest.fn(),
    });
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('dismisses click with no href', () => {
    // If no href is set, it should prevent default
    const preventDefault = jest.fn();
    shallow(<Button />).simulate('click', {
      preventDefault,
      stopPropagation: jest.fn(),
    });
    expect(preventDefault).toHaveBeenCalledTimes(1);
  });

  it('does not dismiss click if href is set', () => {
    const preventDefault = jest.fn();
    shallow(<Button href="/admin/" />).simulate('click', {
      preventDefault,
      stopPropagation: jest.fn(),
    });
    expect(preventDefault).toHaveBeenCalledTimes(0);
  });

  it('calls navigate instead of default behaviour if provided', () => {
    // If "href" and a navigate handler is provided, it should call that navigate handler and prevent default
    const preventDefault = jest.fn();
    const navigate = jest.fn();

    shallow(<Button href="/admin/" navigate={navigate} />).simulate('click', {
      preventDefault,
      stopPropagation: jest.fn(),
    });
    expect(preventDefault).toHaveBeenCalledTimes(1);
    expect(navigate).toHaveBeenCalledTimes(1);
    expect(navigate).toHaveBeenCalledWith('/admin/');
  });
});
