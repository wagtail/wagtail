import { shallow } from 'enzyme';
import React from 'react';
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

  it('should not call dispatch when closed via FocusTrap deactivation (onCloseExplorer no longer resets navigation path)', () => {
    // Regression: previously onCloseExplorer dispatched set-navigation-path ''
    // which re-triggered the useEffect feedback loop causing the panel to reopen.
    // The dispatch was removed; only the setTimeout cleanup now runs.
    const dispatch = jest.fn();

    const wrapper = shallow(
      <PageExplorerMenuItem
        dispatch={dispatch}
        item={{}}
        path=".explorer"
        state={{ activePath: '', navigationPath: '.explorer' }}
      />,
    );

    wrapper.find('Connect(PageExplorer)').prop('onClose')();

    expect(dispatch).not.toHaveBeenCalled();
  });

  it('should ignore a second onClose call while already closing (isClosing ref guard)', () => {
    // Regression: clicking the sidebar button triggered both onClick and
    // FocusTrap.onDeactivate, causing onCloseExplorer to run twice and
    // re-open the panel. The isClosing ref guard blocks the second call.
    const dispatch = jest.fn();

    const wrapper = shallow(
      <PageExplorerMenuItem
        dispatch={dispatch}
        item={{}}
        path=".explorer"
        state={{ activePath: '', navigationPath: '.explorer' }}
      />,
    );

    const onClose = wrapper.find('Connect(PageExplorer)').prop('onClose');

    // First call — should proceed normally (no dispatch, just setTimeout)
    onClose();
    const callCountAfterFirst = dispatch.mock.calls.length;

    // Second call — isClosing ref is true, must be a no-op
    onClose();

    expect(dispatch.mock.calls.length).toBe(callCountAfterFirst);
  });
});
