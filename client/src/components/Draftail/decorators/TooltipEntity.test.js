import React from 'react';
import { shallow } from 'enzyme';

import TooltipEntity from './TooltipEntity';

describe('TooltipEntity', () => {
  it('works', () => {
    expect(
      shallow(
        <TooltipEntity
          entityKey="1"
          onEdit={() => {}}
          onRemove={() => {}}
          icon="#icon-test"
          url="https://www.example.com/"
          label="www.example.com"
        >
          test
        </TooltipEntity>,
      ),
    ).toMatchSnapshot();
  });

  it('shortened label', () => {
    const wrapper = shallow(
      <TooltipEntity
        entityKey="1"
        onEdit={() => {}}
        onRemove={() => {}}
        icon="#icon-test"
        url="https://www.example.com/"
        label="www.example.example.example.com"
      >
        test
      </TooltipEntity>,
    );

    expect(shallow(wrapper.instance().renderTooltip()).find('a').text()).toBe(
      'www.example.example.…',
    );
  });

  it('empty label', () => {
    const wrapper = shallow(
      <TooltipEntity
        entityKey="1"
        onEdit={() => {}}
        onRemove={() => {}}
        icon="#icon-test"
        url="https://www.example.com/"
        label=""
      >
        test
      </TooltipEntity>,
    );

    expect(shallow(wrapper.instance().renderTooltip()).find('a')).toHaveLength(
      0,
    );
  });

  it('#openTooltip', () => {
    const wrapper = shallow(
      <TooltipEntity
        entityKey="1"
        onEdit={() => {}}
        onRemove={() => {}}
        icon="#icon-test"
        url="https://www.example.com/"
        label="www.example.com"
      >
        test
      </TooltipEntity>,
    );

    const target = document.createElement('div');
    target.setAttribute('data-draftail-trigger', true);
    document.body.appendChild(target);
    document.body.setAttribute('data-draftail-editor-wrapper', true);

    wrapper.find('.TooltipEntity').simulate('mouseup', {
      target: target,
    });

    expect(wrapper).toMatchSnapshot();
  });
});
