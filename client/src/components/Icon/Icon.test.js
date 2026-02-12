import React from 'react';
import { shallow, mount } from 'enzyme';
import Icon from './Icon';

describe('Icon', () => {
  it('exists', () => {
    expect(Icon).toBeDefined();
  });

  it('should support icons with a name', () => {
    const wrapper = mount(<Icon name="test" />);

    expect(wrapper.find('.icon.icon-test')).toHaveLength(1);
    expect(wrapper.find('use[href="#icon-test"]')).toHaveLength(1);

    expect(wrapper).toMatchSnapshot();
  });

  it('should support children in place of the icon use#name', () => {
    const wrapper = shallow(
      <icon name="example">
        <rect
          x="10"
          y="10"
          width="30"
          height="30"
          stroke="black"
          fill="transparent"
          strokeWidth="5"
        />
      </icon>,
    );

    expect(wrapper.find('use')).toHaveLength(0);
    expect(wrapper.find('rect')).toHaveLength(1);
  });

  it('should support a className prop', () => {
    const wrapper = mount(<Icon name="test" className="u-test" />);

    expect(wrapper.find('.icon.u-test')).toHaveLength(1);
  });

  it('should support other svg attributes', () => {
    const wrapper = mount(<Icon name="test" viewBox="0 0 1024 1024" />);

    expect(wrapper.find('svg').prop('viewBox')).toBe('0 0 1024 1024');
  });

  it('should support a title that is output as a sibling of the title', () => {
    const wrapper = mount(<Icon name="test" title="Test title" />);

    const title = wrapper.find('svg.icon ~ span');
    expect(title).toHaveLength(1);

    expect(title.text()).toBe('Test title');
    expect(title.hasClass('w-sr-only')).toBe(true);
  });
});
