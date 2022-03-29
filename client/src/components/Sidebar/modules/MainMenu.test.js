import React from 'react';
import { shallow } from 'enzyme';
import { Menu } from './MainMenu';

describe('Menu', () => {
  const strings = {};
  const user = { avatarUrl: 'https://gravatar/profile' };
  const onAccountExpand = jest.fn();

  it('should render with the minimum required props', () => {
    const wrapper = shallow(
      <Menu
        accountMenuItems={[]}
        menuItems={[]}
        strings={strings}
        user={user}
        onAccountExpand={onAccountExpand}
      />,
    );

    expect(wrapper).toMatchSnapshot();
  });

  it('should toggle the sidebar footer (account) when clicked', () => {
    const wrapper = shallow(
      <Menu
        accountMenuItems={[]}
        menuItems={[]}
        strings={strings}
        user={user}
        onAccountExpand={onAccountExpand}
      />,
    );

    // default is closed
    expect(wrapper.find('.sidebar-footer__account').prop('aria-expanded')).toBe(
      'false',
    );
    expect(wrapper.find('.sidebar-footer--open')).toHaveLength(0);

    wrapper.find('.sidebar-footer__account').simulate('click');

    expect(wrapper.find('.sidebar-footer__account').prop('aria-expanded')).toBe(
      'true',
    );
    expect(wrapper.find('.sidebar-footer--open')).toHaveLength(1);
  });
});
