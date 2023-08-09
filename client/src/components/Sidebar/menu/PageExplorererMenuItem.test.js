import React from 'react';
import { shallow } from 'enzyme';
import { PageExplorerMenuItem } from './PageExplorerMenuItem';

describe('PageExplorerMenuItem', () => {
  const state = { activePath: '.reports.workflows', navigationPath: '' };

  it('should render with the minimum required props', () => {
    const wrapper = shallow(
      <PageExplorerMenuItem item={{}} path=".explorer" state={state} />,
    );

    expect(wrapper).toMatchSnapshot();
  });

  it('should expand the explorer menu when clicked', () => {
    const dispatch = jest.fn();
    const preventDefault = jest.fn();

    const wrapper = shallow(
      <PageExplorerMenuItem
        dispatch={dispatch}
        item={{}}
        path=".explorer"
        state={state}
      />,
    );

    expect(
      wrapper.find('.sidebar-menu-item__link').prop('aria-expanded'),
    ).toEqual('false');
    expect(wrapper.find('SidebarPanel').prop('isOpen')).toBe(false);
    expect(dispatch).not.toHaveBeenCalled();
    expect(preventDefault).not.toHaveBeenCalled();

    // click the button
    wrapper
      .find('.sidebar-menu-item__link')
      .simulate('click', { preventDefault });

    expect(dispatch).toHaveBeenCalledWith({
      path: '.explorer',
      type: 'set-navigation-path',
    });
    expect(preventDefault).not.toHaveBeenCalled();

    // manually update the state as if the redux action was dispatched
    wrapper.setProps({
      state: { activePath: '.reports.workflows', navigationPath: '.explorer' },
    });

    // check that the expanded state is working
    expect(
      wrapper.find('.sidebar-menu-item__link').prop('aria-expanded'),
    ).toEqual('true');
    expect(wrapper.find('SidebarPanel').prop('isOpen')).toBe(true);

    // click the button to close
    wrapper
      .find('.sidebar-menu-item__link')
      .simulate('click', { preventDefault });

    expect(dispatch).toHaveBeenCalledTimes(2);
    expect(dispatch).toHaveBeenLastCalledWith({
      path: '',
      type: 'set-navigation-path',
    });
    expect(preventDefault).not.toHaveBeenCalled();
  });
});
