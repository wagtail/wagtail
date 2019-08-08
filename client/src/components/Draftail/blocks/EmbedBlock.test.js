import React from 'react';
import { shallow } from 'enzyme';

import EmbedBlock from '../blocks/EmbedBlock';

describe('EmbedBlock', () => {
  it('renders', () => {
    expect(
      shallow(
        <EmbedBlock
          blockProps={{
            entityType: {},
            entity: {
              getData: () => ({
                url: 'http://www.example.com/',
                title: 'Test title',
                thumbnail: 'http://www.example.com/example.png',
              }),
            },
          }}
        />
      )
    ).toMatchSnapshot();
  });

  it('no data', () => {
    expect(
      shallow(
        <EmbedBlock
          blockProps={{
            entityType: {},
            entity: {
              getData: () => ({}),
            },
          }}
        />
      )
    ).toMatchSnapshot();
  });
});
