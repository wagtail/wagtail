import React from 'react';
import { shallow } from 'enzyme';
import {
  convertFromRaw,
  EditorState,
  ContentState,
  convertFromHTML,
} from 'draft-js';

import Link, { getLinkAttributes, getValidURL, onPasteLink } from './Link';

describe('Link', () => {
  it('works', () => {
    const content = convertFromRaw({
      entityMap: {
        1: {
          type: 'LINK',
          data: {
            url: 'http://www.example.com/',
          },
          mutability: 'MUTABLE',
        },
      },
      blocks: [
        {
          key: 'a',
          text: 'test',
          type: 'unstyled',
          depth: 0,
          inlineStyleRanges: [],
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
        <Link
          contentState={content}
          entityKey="1"
          onEdit={() => {}}
          onRemove={() => {}}
        >
          test
        </Link>,
      ),
    ).toMatchSnapshot();
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

    it('phone', () => {
      expect(getLinkAttributes({ url: 'tel:+46700000000' })).toMatchObject({
        url: 'tel:+46700000000',
        label: '+46700000000',
      });
    });

    it('anchor', () => {
      expect(getLinkAttributes({ url: '#testanchor' })).toMatchObject({
        url: '#testanchor',
        label: '#testanchor',
      });
    });

    it('external', () => {
      expect(getLinkAttributes({ url: 'http://www.ex.com/' })).toMatchObject({
        url: 'http://www.ex.com/',
        label: 'www.ex.com',
      });
    });

    it('no data', () => {
      expect(getLinkAttributes({})).toMatchObject({
        url: null,
        label: 'Broken link',
      });
    });
  });
});

describe.each`
  text                           | result
  ${'test@example.com'}          | ${'mailto:test@example.com'}
  ${'test@example'}              | ${false}
  ${'test@.com'}                 | ${false}
  ${'mailto:test@.com'}          | ${false}
  ${'example.com'}               | ${false}
  ${'http://example.com'}        | ${'http://example.com'}
  ${'https://example.com'}       | ${'https://example.com'}
  ${'ftp://example.com'}         | ${'ftp://example.com'}
  ${'ftps://example.com'}        | ${'ftps://example.com'}
  ${'//example.com'}             | ${false}
  ${'https://example.com/#test'} | ${'https://example.com/#test'}
  ${'example'}                   | ${false}
  ${'03069990000'}               | ${false}
  ${'tel:03069990000'}           | ${false}
  ${'file://test'}               | ${false}
`('getValidURL', ({ text, result }) => {
  test(text, () => {
    expect(getValidURL(text)).toBe(result);
  });
});

describe('onPasteLink', () => {
  let editorState;
  let setEditorState;

  beforeEach(() => {
    const { contentBlocks } = convertFromHTML('<p>hello</p>');
    const contentState = ContentState.createFromBlockArray(contentBlocks);
    editorState = EditorState.createWithContent(contentState);

    setEditorState = jest.fn((state) => state);
  });

  it('discards invalid URLs', () => {
    expect(onPasteLink('test', null, editorState, { setEditorState })).toBe(
      'not-handled',
    );
    expect(setEditorState).not.toHaveBeenCalled();
  });

  it('creates link onto selected text', () => {
    const selection = editorState.getSelection().merge({
      focusOffset: 4,
    });
    const selected = EditorState.forceSelection(editorState, selection);
    expect(
      onPasteLink('https://example.com/selected', null, selected, {
        setEditorState,
      }),
    ).toBe('handled');
    expect(setEditorState).toHaveBeenCalled();
    const content: ContentState =
      setEditorState.mock.calls[0][0].getCurrentContent();
    expect(content.getFirstBlock().getText()).toBe('hello');
    expect(content.getFirstBlock().getText()).toBe('hello');
    expect(
      content.getEntity(content.getLastCreatedEntityKey()).getData().url,
    ).toBe('https://example.com/selected');
  });

  it('creates link with paste as link text when collapsed', () => {
    expect(
      onPasteLink('https://example.com/collapsed', null, editorState, {
        setEditorState,
      }),
    ).toBe('handled');
    expect(setEditorState).toHaveBeenCalled();
    const content: ContentState =
      setEditorState.mock.calls[0][0].getCurrentContent();
    expect(content.getFirstBlock().getText()).toBe(
      'https://example.com/collapsedhello',
    );
    expect(
      content.getEntity(content.getLastCreatedEntityKey()).getData().url,
    ).toBe('https://example.com/collapsed');
  });
});
