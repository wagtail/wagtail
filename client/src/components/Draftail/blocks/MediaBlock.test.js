import React from 'react';
import { shallow } from 'enzyme';

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

  describe('tooltip', () => {
    let wrapper;

    beforeEach(() => {
      wrapper = shallow(
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
      );
    });

    it('opens', () => {
      const target = document.createElement('div');
      document.body.appendChild(target);

      wrapper.simulate('mouseup', { target });

      expect(
        wrapper
          .find('Portal')
          .dive()
          .instance().portal
      ).toMatchSnapshot();
    });

    it.skip('large viewport', () => {
      const target = document.createElement('div');
      document.body.appendChild(target);
      target.getBoundingClientRect = () => ({
        top: 0,
        left: 0,
        width: -600,
        height: 0,
      });

      wrapper.simulate('mouseup', { target });

      expect(
        wrapper
          .find('Portal')
          .dive()
          .instance()
          .portal.querySelector('.Tooltip').className
      ).toBe('Tooltip Tooltip--left');
    });

    it('closes', () => {
      const target = document.createElement('div');
      document.body.appendChild(target);

      jest.spyOn(target, 'getBoundingClientRect');

      expect(wrapper.state('showTooltipAt')).toBe(null);

      wrapper.simulate('mouseup', { target });

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
