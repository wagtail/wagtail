import { shallow } from 'enzyme';
import React from 'react';
import Minimap from './Minimap';

const makeContainer = (id: string) => {
  const el = document.createElement('div');
  el.id = id;
  return el;
};

const defaultProps = {
  container: makeContainer('container'),
  anchorsContainer: makeContainer('tab-content'),
  links: [],
  onUpdate: () => {},
  toggleAllPanels: () => {},
};

describe('Minimap', () => {
  it('exists', () => {
    expect(Minimap).toBeDefined();
  });

  it('defaults to expanded on first render and on new tabs', () => {
    const tab1 = makeContainer('tab-content');
    const tab2 = makeContainer('tab-promote');
    const wrapper = shallow(
      <Minimap {...defaultProps} anchorsContainer={tab1} />,
    );

    expect(wrapper.find('CollapseAll').prop('expanded')).toBe(true);

    wrapper.find('CollapseAll').prop('onClick')();
    expect(wrapper.find('CollapseAll').prop('expanded')).toBe(false);

    wrapper.setProps({ anchorsContainer: tab2 });
    expect(wrapper.find('CollapseAll').prop('expanded')).toBe(true);
  });

  it('preserves and isolates state per tab', () => {
    const tab1 = makeContainer('tab-content');
    const tab2 = makeContainer('tab-promote');
    const wrapper = shallow(
      <Minimap {...defaultProps} anchorsContainer={tab1} />,
    );

    wrapper.find('CollapseAll').prop('onClick')();

    wrapper.setProps({ anchorsContainer: tab2 });
    wrapper.find('CollapseAll').prop('onClick')();
    expect(wrapper.find('CollapseAll').prop('expanded')).toBe(false);

    wrapper.setProps({ anchorsContainer: tab1 });
    expect(wrapper.find('CollapseAll').prop('expanded')).toBe(false);
  });
});
