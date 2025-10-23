/* eslint-disable jsx-a11y/anchor-is-valid */
import React from 'react';
import { shallow } from 'enzyme';

import Link from './Link';

describe('Link', () => {
  it('exists', () => {
    expect(Link).toBeDefined();
  });

  it('basic', () => {
    expect(shallow(<Link />)).toMatchSnapshot();
  });

  it('#children', () => {
    expect(shallow(<Link>To infinity and beyond!</Link>)).toMatchSnapshot();
  });

  it('#accessibleLabel', () => {
    expect(
      shallow(<Link accessibleLabel="I am here in the shadows" />),
    ).toMatchSnapshot();
  });

  it('#target', () => {
    expect(
      shallow(<Link target="_blank" rel="noreferrer" />),
    ).toMatchSnapshot();
  });

  it('is clickable', () => {
    const onClick = jest.fn();
    shallow(<Link onClick={onClick} />).simulate('click', {
      preventDefault: jest.fn(),
      stopPropagation: jest.fn(),
    });
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('dismisses click with no href', () => {
    // If no href is set, it should prevent default
    const preventDefault = jest.fn();
    shallow(<Link />).simulate('click', {
      preventDefault,
      stopPropagation: jest.fn(),
    });
    expect(preventDefault).toHaveBeenCalledTimes(1);
  });

  it('does not dismiss click if href is set', () => {
    const preventDefault = jest.fn();
    shallow(<Link href="/admin/" />).simulate('click', {
      preventDefault,
      stopPropagation: jest.fn(),
    });
    expect(preventDefault).toHaveBeenCalledTimes(0);
  });

  it('calls navigate instead of default behavior if provided', () => {
    // If "href" and a navigate handler is provided, it should call that navigate handler and prevent default
    const preventDefault = jest.fn();
    const navigate = jest.fn();

    shallow(<Link href="/admin/" navigate={navigate} />).simulate('click', {
      preventDefault,
      stopPropagation: jest.fn(),
    });
    expect(preventDefault).toHaveBeenCalledTimes(1);
    expect(navigate).toHaveBeenCalledTimes(1);
    expect(navigate).toHaveBeenCalledWith('/admin/');
  });
});
