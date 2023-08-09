import React from 'react';
import { shallow } from 'enzyme';
import { convertFromRaw } from 'draft-js';

import Document from './Document';

describe('Document', () => {
  it('works', () => {
    const content = convertFromRaw({
      entityMap: {
        1: {
          type: 'DOCUMENT',
          data: {
            url: '/example.pdf',
            filename: 'example.pdf',
          },
        },
      },
      blocks: [
        {
          key: 'a',
          text: 'test',
          entityRanges: [
            {
              offset: 0,
              length: 4,
              key: 0,
            },
          ],
        },
      ],
    });
    expect(
      shallow(
        <Document
          contentState={content}
          entityKey="1"
          onEdit={() => {}}
          onRemove={() => {}}
        >
          test
        </Document>,
      ),
    ).toMatchSnapshot();
  });

  it('no data', () => {
    const content = convertFromRaw({
      entityMap: {
        2: {
          type: 'DOCUMENT',
        },
      },
      blocks: [
        {
          key: 'a',
          text: 'test',
          entityRanges: [
            {
              offset: 0,
              length: 4,
              key: 0,
            },
          ],
        },
      ],
    });
    expect(
      shallow(
        <Document
          contentState={content}
          entityKey="2"
          onEdit={() => {}}
          onRemove={() => {}}
        >
          test
        </Document>,
      ),
    ).toMatchSnapshot();
  });
});
