import { shallow } from 'enzyme';
import React from 'react';

import { noop } from '../../../utils/noop';
import EmbedBlock from './EmbedBlock';

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
