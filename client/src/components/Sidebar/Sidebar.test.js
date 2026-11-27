import { mount, shallow } from 'enzyme';
import React from 'react';
import { Sidebar } from './Sidebar';

describe('Sidebar', () => {
  it('tracks message height and stops observing on unmount', () => {
    const messages = document.createElement('div');
    messages.className = 'messages';
    document.body.appendChild(messages);
    let height = 70;
    Object.defineProperty(messages, 'offsetHeight', { get: () => height });

    const originalResizeObserver = global.ResizeObserver;
    const observe = jest.fn();
    const disconnect = jest.fn();
    let resize;
    global.ResizeObserver = jest.fn((callback) => {
      resize = callback;
      return { observe, disconnect };
    });

    const wrapper = mount(<Sidebar modules={[]} />);
    const toggle = wrapper.find('.sidebar-nav-toggle').getDOMNode();
    expect(observe).toHaveBeenCalledWith(messages);
    expect(toggle.style.getPropertyValue('--w-messages-height')).toBe('70px');

    height = 140;
    resize();
    expect(toggle.style.getPropertyValue('--w-messages-height')).toBe('140px');

    height = 0;
    resize();
    expect(toggle.style.getPropertyValue('--w-messages-height')).toBe('0px');

    wrapper.unmount();
    expect(disconnect).toHaveBeenCalledTimes(1);
    messages.remove();
    global.ResizeObserver = originalResizeObserver;
  });

  it('should render with the minimum required props', () => {
    const wrapper = shallow(<Sidebar modules={[]} />);

    expect(wrapper).toMatchSnapshot();
  });

  it('should toggle the slim mode in the sidebar when outer button clicked', () => {
    const onExpandCollapse = jest.fn();

    const wrapper = shallow(
      <Sidebar modules={[]} onExpandCollapse={onExpandCollapse} />,
    );

    // default expanded (non-slim)
    expect(
      wrapper.find('.sidebar__collapse-toggle').prop('aria-expanded'),
    ).toEqual('true');
    expect(wrapper.find('.sidebar--slim')).toHaveLength(0);
    expect(onExpandCollapse).not.toHaveBeenCalled();

    // toggle slim mode
    wrapper.find('.sidebar__collapse-toggle').simulate('click');

    expect(
      wrapper.find('.sidebar__collapse-toggle').prop('aria-expanded'),
    ).toEqual('false');
    expect(wrapper.find('.sidebar--slim')).toHaveLength(1);
    expect(onExpandCollapse).toHaveBeenCalledWith(true);
  });

  it('should toggle the sidebar visibility on click (used on mobile)', () => {
    const onExpandCollapse = jest.fn();

    const wrapper = shallow(
      <Sidebar modules={[]} onExpandCollapse={onExpandCollapse} />,
    );

    // default not expanded
    expect(wrapper.find('.sidebar-nav-toggle').prop('aria-expanded')).toEqual(
      'false',
    );
    expect(wrapper.find('.sidebar-nav-toggle--open')).toHaveLength(0);

    // toggle expanded mode
    wrapper.find('.sidebar-nav-toggle').simulate('click');

    // check it is expanded
    expect(wrapper.find('.sidebar-nav-toggle').prop('aria-expanded')).toEqual(
      'true',
    );
    expect(wrapper.find('.sidebar-nav-toggle--open')).toHaveLength(1);
  });
});
