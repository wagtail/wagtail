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
    expect(
      shallow(
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
      )
        .setState({
          showTooltipAt: document.createElement('div').getBoundingClientRect(),
        })
        .find('Tooltip a')
        .text(),
    ).toBe('www.example.example.…');
  });

  it('empty label', () => {
    expect(
      shallow(
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
      )
        .setState({
          showTooltipAt: document.createElement('div').getBoundingClientRect(),
        })
        .find('Tooltip a').length,
    ).toBe(0);
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

  it('#closeTooltip', () => {
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

    wrapper.find('.TooltipEntity').simulate('mouseup', {
      target: document.createElement('div'),
    });

    wrapper.instance().closeTooltip();

    expect(wrapper.state()).toEqual({
      showTooltipAt: null,
    });
  });

  it('#onEdit', () => {
    const onEdit = jest.fn();

    const wrapper = shallow(
      <TooltipEntity
        entityKey="1"
        onEdit={onEdit}
        onRemove={() => {}}
        icon="#icon-test"
        url="https://www.example.com/"
        label="www.example.com"
      >
        test
      </TooltipEntity>,
    );

    wrapper.instance().onEdit(new Event('click'));

    expect(onEdit).toHaveBeenCalled();
  });

  it('#onRemove', () => {
    const onRemove = jest.fn();

    const wrapper = shallow(
      <TooltipEntity
        entityKey="1"
        onEdit={() => {}}
        onRemove={onRemove}
        icon="#icon-test"
        url="https://www.example.com/"
        label="www.example.com"
      >
        test
      </TooltipEntity>,
    );

    wrapper.instance().onRemove(new Event('click'));

    expect(onRemove).toHaveBeenCalled();
  });
});
