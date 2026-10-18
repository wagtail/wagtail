import { mount, shallow } from 'enzyme';
import React from 'react';

import PageExplorerHeader from './PageExplorerHeader';

const mockProps = {
  page: {
    meta: {
      depth: 3,
      parent: {
        id: 1,
      },
    },
  },
  depth: 2,
  onClick: jest.fn(),
};

describe('PageExplorerHeader', () => {
  it('exists', () => {
    expect(PageExplorerHeader).toBeDefined();
  });

  it('basic', () => {
    expect(shallow(<PageExplorerHeader {...mockProps} />)).toMatchSnapshot();
  });

  it('#depth at root', () => {
    expect(
      shallow(<PageExplorerHeader {...mockProps} depth={0} />),
    ).toMatchSnapshot();
  });

  it('#page', () => {
    const wrapper = shallow(
      <PageExplorerHeader
        {...mockProps}
        page={{
          id: 'a',
          admin_display_title: 'test',
          meta: { depth: 3, parent: { id: 1 } },
        }}
      />,
    );
    expect(wrapper).toMatchSnapshot();
  });

  it('shows "Pages" instead of the root page title', () => {
    const wrapper = shallow(
      <PageExplorerHeader
        {...mockProps}
        depth={0}
        page={{
          id: 1,
          admin_display_title: 'Root',
          meta: { depth: 1, parent: null },
        }}
      />,
    );
    expect(
      wrapper.find('.c-page-explorer__header__title__inner span').text(),
    ).toBe('Pages');
  });

  it('#onClick', () => {
    const wrapper = mount(<PageExplorerHeader {...mockProps} />);
    wrapper.find('Link').simulate('click');

    expect(mockProps.onClick).toHaveBeenCalledTimes(1);
  });
});
