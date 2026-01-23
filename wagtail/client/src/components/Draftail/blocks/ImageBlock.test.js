import React from 'react';
import { shallow } from 'enzyme';

import ImageBlock from './ImageBlock';

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
        />,
      ),
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
        />,
      ),
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
        />,
      ),
    ).toMatchSnapshot();
  });
});
