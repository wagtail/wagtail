import React from 'react';
import { shallow } from 'enzyme';
import { SubMenuItem } from './SubMenuItem';

describe('SubMenuItem', () => {
  const state = { activePath: '.reports.workflows', navigationPath: '' };

  it('should render with the minimum required props', () => {
    const wrapper = shallow(
      <SubMenuItem
        item={{ classNames: '', menuItems: [] }}
        items={[]}
        state={state}
        path=".reports"
      />,
    );

    expect(wrapper).toMatchSnapshot();
  });

  it('should provide a button to expand the sub-menu', () => {
    const dispatch = jest.fn();

    const wrapper = shallow(
      <SubMenuItem
        dispatch={dispatch}
        item={{ classNames: '', menuItems: [] }}
        items={[]}
        state={state}
        path=".reports"
      />,
    );

    expect(wrapper.find('.sidebar-menu-item__link').prop('aria-expanded')).toBe(
      'false',
    );
    expect(dispatch).not.toHaveBeenCalled();
    expect(wrapper.find('.sidebar-sub-menu-item--open')).toHaveLength(0);

    // click the sub menu item
    wrapper.find('.sidebar-menu-item__link').simulate('click');

    // check the dispatch function (redux state) was called
    expect(dispatch).toHaveBeenCalledWith({
      path: '.reports',
      type: 'set-navigation-path',
    });

    // manually update the state as if the redux action was dispatched
    wrapper.setProps({
      state: { navigationPath: '.reports', activePath: '.reports.workflows' },
    });

    expect(wrapper.find('.sidebar-menu-item__link').prop('aria-expanded')).toBe(
      'true',
    );
    expect(wrapper.find('.sidebar-sub-menu-item--open')).toHaveLength(1);

    // click a second time to 'close'
    wrapper.find('.sidebar-menu-item__link').simulate('click');

    expect(dispatch).toHaveBeenCalledTimes(2);
    expect(dispatch).toHaveBeenLastCalledWith({
      path: '',
      type: 'set-navigation-path',
    });
  });
});
