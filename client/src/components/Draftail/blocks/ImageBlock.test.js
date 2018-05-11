import React from 'react';
import { shallow } from 'enzyme';

import { DraftUtils } from 'draftail';

import ImageBlock from '../blocks/ImageBlock';

describe('ImageBlock', () => {
  it('renders', () => {
    expect(
      shallow(
        <ImageBlock
          block={{}}
          blockProps={{
            editorState: {},
            entityType: {},
            entity: {
              getData: () => ({
                src: 'example.png',
              }),
            },
            onChange: () => {},
          }}
        />
      )
    ).toMatchSnapshot();
  });

  it('no data', () => {
    expect(
      shallow(
        <ImageBlock
          block={{}}
          blockProps={{
            editorState: {},
            entityType: {},
            entity: {
              getData: () => ({}),
            },
            onChange: () => {},
          }}
        />
      )
    ).toMatchSnapshot();
  });

  it('alt', () => {
    expect(
      shallow(
        <ImageBlock
          block={{}}
          blockProps={{
            editorState: {},
            entityType: {},
            entity: {
              getData: () => ({
                src: 'example.png',
                alt: 'Test',
              }),
            },
            onChange: () => {},
          }}
        />
      )
    ).toMatchSnapshot();
  });

  it('changeAlt', () => {
    jest.spyOn(DraftUtils, 'updateBlockEntity');
    DraftUtils.updateBlockEntity.mockImplementation(e => e);

    const onChange = jest.fn();
    const wrapper = shallow(
      <ImageBlock
        block={{}}
        blockProps={{
          editorState: {},
          entityType: {},
          entity: {
            getData: () => ({
              src: 'example.png',
              alt: 'Test',
            }),
          },
          onChange,
        }}
      />
    );

    // // Alt field is readonly for now.
    wrapper.instance().changeAlt({
      target: {
        value: 'new alt',
      }
    });
    // wrapper.find('[type="text"]').simulate('change', {
    //   target: {
    //     value: 'new alt',
    //   },
    // });

    expect(onChange).toHaveBeenCalled();
    expect(DraftUtils.updateBlockEntity).toHaveBeenCalledWith(
      expect.any(Object),
      {},
      expect.objectContaining({ alt: 'new alt' })
    );

    DraftUtils.updateBlockEntity.mockRestore();
  });
});
