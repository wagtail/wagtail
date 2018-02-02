import React from 'react';
import { shallow } from 'enzyme';

import TooltipEntity from './TooltipEntity';

describe('TooltipEntity', () => {
  it('works', () => {
    expect(shallow((
      <TooltipEntity
        entityKey="1"
        onEdit={() => {}}
        onRemove={() => {}}
        icon="#icon-test"
        url="https://www.example.com/"
        label="www.example.com"
      >
        test
      </TooltipEntity>
    ))).toMatchSnapshot();
  });

  it('shortened label', () => {
    expect(shallow((
      <TooltipEntity
        entityKey="1"
        onEdit={() => {}}
        onRemove={() => {}}
        icon="#icon-test"
        url="https://www.example.com/"
        label="www.example.example.example.com"
      >
        test
      </TooltipEntity>
    )).setState({
      showTooltipAt: document.createElement('div').getBoundingClientRect(),
    }).find('Tooltip a')
      .text()).toBe('www.example.example.…');
  });

  it('#openTooltip', () => {
    const wrapper = shallow((
      <TooltipEntity
        entityKey="1"
        onEdit={() => {}}
        onRemove={() => {}}
        icon="#icon-test"
        url="https://www.example.com/"
        label="www.example.com"
      >
        test
      </TooltipEntity>
    ));

    wrapper.find('.TooltipEntity').simulate('mouseup', {
      target: document.createElement('div'),
    });

    expect(wrapper).toMatchSnapshot();
  });

  it('#closeTooltip', () => {
    const wrapper = shallow((
      <TooltipEntity
        entityKey="1"
        onEdit={() => {}}
        onRemove={() => {}}
        icon="#icon-test"
        url="https://www.example.com/"
        label="www.example.com"
      >
        test
      </TooltipEntity>
    ));

    wrapper.find('.TooltipEntity').simulate('mouseup', {
      target: document.createElement('div'),
    });

    wrapper.instance().closeTooltip();

    expect(wrapper.state()).toEqual({
      showTooltipAt: null,
    });
  });
});
