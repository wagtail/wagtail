import React from 'react';
import { shallow } from 'enzyme';

import EmbedBlock from './EmbedBlock';
import { noop } from '../../../utils/noop';

describe('EmbedBlock', () => {
  it('renders', () => {
    expect(
      shallow(
        <EmbedBlock
          block={{}}
          blockProps={{
            editorState: {},
            entityType: {},
            entity: {
              getData: () => ({
                url: 'http://www.example.com/',
                title: 'Test title',
                thumbnail: 'http://www.example.com/example.png',
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
        <EmbedBlock
          block={{}}
          blockProps={{
            editorState: {},
            entityType: {},
            entity: {
              getData: () => ({}),
            },
            onChange: noop,
          }}
        />,
      ),
    ).toMatchSnapshot();
  });
});
