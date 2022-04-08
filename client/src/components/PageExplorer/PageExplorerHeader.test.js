import React from 'react';
import { mount, shallow } from 'enzyme';

import PageExplorerHeader from './PageExplorerHeader';

const mockProps = {
  page: {
    meta: {
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
          meta: { parent: { id: 1 } },
        }}
      />,
    );
    expect(wrapper).toMatchSnapshot();
  });

  it('#onClick', () => {
    const wrapper = mount(<PageExplorerHeader {...mockProps} />);
    wrapper.find('Button').simulate('click');

    expect(mockProps.onClick).toHaveBeenCalledTimes(1);
  });
});
