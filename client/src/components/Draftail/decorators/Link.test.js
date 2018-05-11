import React from 'react';
import { shallow } from 'enzyme';
import { convertFromRaw } from 'draft-js';

import Link, { getLinkAttributes } from './Link';

describe('Link', () => {
  it('works', () => {
    const content = convertFromRaw({
      entityMap: {
        1: {
          type: 'LINK',
          data: {
            url: 'http://www.example.com/',
          },
        }
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
            }
          ]
        }
      ]
    });
    expect(shallow((
      <Link
        contentState={content}
        entityKey="1"
        onEdit={() => {}}
        onRemove={() => {}}
      >
        test
      </Link>
    ))).toMatchSnapshot();
  });

  describe('getLinkAttributes', () => {
    it('page', () => {
      expect(getLinkAttributes({ id: '1', url: '/' })).toMatchObject({
        url: '/',
        label: '/',
      });
    });

    it('mail', () => {
      expect(getLinkAttributes({ url: 'mailto:test@ex.com' })).toMatchObject({
        url: 'mailto:test@ex.com',
        label: 'test@ex.com',
      });
    });

    it('external', () => {
      expect(getLinkAttributes({ url: 'http://www.ex.com/' })).toMatchObject({
        url: 'http://www.ex.com/',
        label: 'www.ex.com',
      });
    });

    it('no data', () => {
      expect(getLinkAttributes({})).toMatchObject({ url: '' });
    });
  });
});
