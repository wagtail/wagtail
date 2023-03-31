import React from 'react';
import { shallow } from 'enzyme';
import CollapseAll from './CollapseAll';

describe('CollapseAll', () => {
  it('exists', () => {
    expect(CollapseAll).toBeDefined();
  });

  it('renders', () => {
    const wrapper = shallow(
      <CollapseAll expanded insideMinimap={false} onClick={() => {}} />,
    );
    expect(wrapper.text()).toBe('<Icon />Collapse all');
    expect(wrapper.find('button').prop('aria-expanded')).toBe(true);
    expect(wrapper.find('Icon').prop('name')).toBe('collapse-up');
  });

  it('renders with expanded set to false', () => {
    const wrapper = shallow(
      <CollapseAll expanded={false} insideMinimap={false} onClick={() => {}} />,
    );
    expect(wrapper.text()).toBe('<Icon />Expand all');
    expect(wrapper.find('button').prop('aria-expanded')).toBe(false);
    expect(wrapper.find('Icon').prop('name')).toBe('collapse-down');
  });
});
