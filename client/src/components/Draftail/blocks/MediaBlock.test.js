import React from 'react';
import { shallow, mount } from 'enzyme';

import MediaBlock from '../blocks/MediaBlock';

describe('MediaBlock', () => {
  it('renders', () => {
    expect(
      shallow(
        <MediaBlock
          src="example.png"
          alt=""
          blockProps={{
            entityType: {
              icon: '#icon-test',
            },
            entity: {
              getData: () => ({
                src: 'example.png',
              }),
            },
          }}
        >
          Test
        </MediaBlock>
      )
    ).toMatchSnapshot();
  });

  it('no data', () => {
    expect(
      shallow(
        <MediaBlock
          src=""
          alt=""
          blockProps={{
            entityType: {
              icon: '#icon-test',
            },
            entity: {
              getData: () => ({}),
            },
          }}
        >
          Test
        </MediaBlock>
      )
    ).toMatchSnapshot();
  });

  describe('tooltip', () => {
    let target;
    let wrapper;

    beforeEach(() => {
      target = document.createElement('div');
      target.setAttribute('data-draftail-trigger', true);
      document.body.appendChild(target);
      document.body.setAttribute('data-draftail-editor-wrapper', true);

      wrapper = mount(
        <MediaBlock
          src="example.png"
          alt=""
          blockProps={{
            entityType: {
              icon: '#icon-test',
            },
            entity: {
              getData: () => ({
                src: 'example.png',
              }),
            },
          }}
        >
          <div id="test">Test</div>
        </MediaBlock>
      );
    });

    it('opens', () => {
      wrapper.simulate('click', { target });

      expect(
        wrapper
          .find('Portal')
          .instance().portal
      ).toMatchSnapshot();
    });

    it('click in tooltip', () => {
      wrapper.simulate('click', { target });

      jest.spyOn(target, 'getBoundingClientRect');

      wrapper.simulate('click', { target: document.querySelector('#test') });

      expect(target.getBoundingClientRect).not.toHaveBeenCalled();
    });

    it('large viewport', () => {
      target.getBoundingClientRect = () => ({
        top: 0,
        left: 0,
        width: -600,
        height: 0,
      });

      wrapper.simulate('click', { target });

      expect(
        wrapper
          .find('Portal')
          .instance()
          .portal.querySelector('.Tooltip').className
      ).toBe('Tooltip Tooltip--left');
    });

    it('closes', () => {
      jest.spyOn(target, 'getBoundingClientRect');

      expect(wrapper.state('showTooltipAt')).toBe(null);

      wrapper.simulate('click', { target });

      expect(wrapper.state('showTooltipAt')).toMatchObject({
        top: 0,
        left: 0,
      });
      expect(target.getBoundingClientRect).toHaveBeenCalled();

      wrapper.instance().closeTooltip();

      expect(wrapper.state('showTooltipAt')).toBe(null);
    });
  });
});
