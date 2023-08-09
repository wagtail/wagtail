import React from 'react';
import { shallow, mount } from 'enzyme';

import { EditorState } from 'draft-js';
import MediaBlock from './MediaBlock';

describe('MediaBlock', () => {
  it('renders', () => {
    expect(
      shallow(
        <MediaBlock
          src="example.png"
          alt=""
          fallbackText="Fallback text"
          block={{}}
          blockProps={{
            editorState: {},
            entityType: {
              icon: '#icon-test',
            },
            entity: {
              getData: () => ({
                src: 'example.png',
              }),
            },
            onChange: () => {},
          }}
        >
          Test
        </MediaBlock>,
      ),
    ).toMatchSnapshot();
  });

  it('no data, with fallback', () => {
    expect(
      shallow(
        <MediaBlock
          src=""
          alt=""
          fallbackText="Fallback text"
          block={{}}
          blockProps={{
            editorState: {},
            entityType: {
              icon: '#icon-test',
            },
            entity: {
              getData: () => ({}),
            },
            onChange: () => {},
          }}
        >
          Test
        </MediaBlock>,
      ),
    ).toMatchSnapshot();
  });

  it('no data, no fallback', () => {
    expect(
      shallow(
        <MediaBlock
          src=""
          alt=""
          fallbackText={null}
          block={{}}
          blockProps={{
            editorState: {},
            entityType: {
              icon: '#icon-test',
            },
            entity: {
              getData: () => ({}),
            },
            onChange: () => {},
          }}
        >
          Test
        </MediaBlock>,
      ),
    ).toMatchSnapshot();
  });

  describe('on click', () => {
    let target;
    let wrapper;
    let blockProps;

    beforeEach(() => {
      target = document.createElement('div');
      target.setAttribute('data-draftail-trigger', true);
      document.body.appendChild(target);
      document.body.setAttribute('data-draftail-editor-wrapper', true);
      blockProps = {
        editorState: EditorState.createEmpty(),
        entityType: {
          icon: '#icon-test',
        },
        entity: {
          getData: () => ({
            src: 'example.png',
          }),
        },
        onChange: () => {},
      };
      wrapper = mount(
        <MediaBlock
          src="example.png"
          alt=""
          fallbackText="Fallback text"
          block={{
            getKey: () => 'abcde',
            getLength: () => 1,
          }}
          blockProps={blockProps}
        >
          <div id="test">Test</div>
        </MediaBlock>,
      );
    });

    it('selected', () => {
      blockProps.onChange = (editorState) => {
        const selecttion = editorState.getSelection();

        expect(selecttion.getAnchorKey()).toEqual('abcde');
        expect(selecttion.getAnchorOffset()).toEqual(0);
        expect(selecttion.getFocusKey()).toEqual('abcde');
        expect(selecttion.getFocusOffset()).toEqual(1);
      };

      jest.spyOn(blockProps, 'onChange');

      wrapper.simulate('click', { target });

      expect(blockProps.onChange).toHaveBeenCalled();
    });

    it('tooltip opens', () => {
      wrapper.simulate('click', { target });

      expect(
        wrapper.find('Portal > Portal').prop('containerInfo'),
      ).toMatchSnapshot();
    });

    it('click in tooltip', () => {
      wrapper.simulate('click', { target });

      jest.spyOn(target, 'getBoundingClientRect');

      wrapper.simulate('click', { target: document.querySelector('#test') });

      expect(target.getBoundingClientRect).not.toHaveBeenCalled();
    });

    it('tooltip in large viewport', () => {
      target.getBoundingClientRect = () => ({
        top: 0,
        left: 0,
        width: -600,
        height: 0,
      });

      wrapper.simulate('click', { target });

      expect(wrapper.find('.Tooltip').prop('className')).toBe(
        'Tooltip Tooltip--left',
      );
    });

    it('tooltip closes', () => {
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
