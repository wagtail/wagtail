import React from 'react';
import { mount, shallow } from 'enzyme';

import ExplorerHeader from './ExplorerHeader';

const mockProps = {
  page: {},
  depth: 2,
  transitionName: 'pop',
  onClick: jest.fn(),
};

describe('ExplorerHeader', () => {
  it('exists', () => {
    expect(ExplorerHeader).toBeDefined();
  });

  it('basic', () => {
    expect(shallow(<ExplorerHeader {...mockProps} />)).toMatchSnapshot();
  });

  it('#depth at root', () => {
    expect(shallow(<ExplorerHeader {...mockProps} depth={1} />)).toMatchSnapshot();
  });

  it('#page', () => {
    const wrapper = shallow(<ExplorerHeader {...mockProps} page={{ id: 'a', admin_display_title: 'test' }} />);
    expect(wrapper).toMatchSnapshot();
  });

  it('#onClick', () => {
    const wrapper = mount(<ExplorerHeader {...mockProps} />);
    wrapper.find('Button').simulate('click');

    expect(mockProps.onClick).toHaveBeenCalledTimes(1);
  });
});
