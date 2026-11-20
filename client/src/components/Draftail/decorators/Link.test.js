import {
  ContentState,
  EditorState,
  Modifier,
  convertFromHTML,
  convertFromRaw,
  convertToRaw,
} from 'draft-js';
import { shallow } from 'enzyme';
import React from 'react';

import Link, { getLinkAttributes, getValidLinkURL, onPasteLink } from './Link';

describe('Link', () => {
  it('works', () => {
    const content = convertFromRaw({
      entityMap: {
        1: {
          type: 'LINK',
          mutability: 'MUTABLE',
          data: {
            url: 'http://www.example.com/',
          },
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
          href="#test"
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
  ${'test@example.com-test'}     | ${false}
  ${'test@example-site.com'}     | ${'mailto:test@example-site.com'}
  ${'test@test.example.com'}     | ${'mailto:test@test.example.com'}
  ${'test@test.example.co.uk'}   | ${'mailto:test@test.example.co.uk'}
  ${'test@xn--ls8h.la'}          | ${'mailto:test@xn--ls8h.la'}
  ${'test@example'}              | ${false}
  ${'test@.com'}                 | ${false}
  ${'mailto:test@.com'}          | ${false}
  ${'example.com'}               | ${false}
  ${'test@example.com-'}         | ${false}
  ${'http://example.com'}        | ${'http://example.com'}
  ${'http://example-site.com'}   | ${'http://example-site.com'}
  ${'http://example.com-test'}   | ${'http://example.com-test'}
  ${'http://test.example.com'}   | ${'http://test.example.com'}
  ${'http://test.example.co.uk'} | ${'http://test.example.co.uk'}
  ${'https://example.com'}       | ${'https://example.com'}
  ${'https://xn--ls8h.la'}       | ${'https://xn--ls8h.la'}
  ${'http://sp.a http://c.e'}    | ${false}
  ${'ftp://example.com'}         | ${'ftp://example.com'}
  ${'ftps://example.com'}        | ${'ftps://example.com'}
  ${'//example.com'}             | ${false}
  ${'https://example.com/#test'} | ${'https://example.com/#test'}
  ${'example'}                   | ${false}
  ${'03069990000'}               | ${false}
  ${'tel:03069990000'}           | ${false}
  ${'file://test'}               | ${false}
`('getValidLinkURL', ({ text, result }) => {
  test(text, () => {
    expect(getValidLinkURL(text)).toBe(result);
  });
});

describe('onPasteLink', () => {
  let editorState;
  let setEditorState;
  let testOnPasteOutput;

  beforeEach(() => {
    const { contentBlocks } = convertFromHTML('<p>hello</p>');
    const contentState = ContentState.createFromBlockArray(contentBlocks);
    editorState = EditorState.createWithContent(contentState);

    setEditorState = jest.fn((state) => state);

    testOnPasteOutput = (text, html) => {
      expect(onPasteLink(text, html, editorState, { setEditorState })).toBe(
        'handled',
      );
      const content = setEditorState.mock.calls[0][0].getCurrentContent();
      return convertToRaw(content);
    };
  });

  it('discards invalid URLs', () => {
    expect(onPasteLink('test', null, editorState, { setEditorState })).toBe(
      'not-handled',
    );
    expect(setEditorState).not.toHaveBeenCalled();
  });

  it('single link onto selected text', () => {
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
    const content = setEditorState.mock.calls[0][0].getCurrentContent();
    expect(content.getFirstBlock().getText()).toBe('hello');
    expect(content.getFirstBlock().getText()).toBe('hello');
    expect(
      content.getEntity(content.getLastCreatedEntityKey()).getData().url,
    ).toBe('https://example.com/selected');
  });

  it('single link without selection', () => {
    expect(
      onPasteLink('https://example.com/collapsed', null, editorState, {
        setEditorState,
      }),
    ).toBe('handled');
    expect(setEditorState).toHaveBeenCalled();
    const content = setEditorState.mock.calls[0][0].getCurrentContent();
    expect(content.getFirstBlock().getText()).toBe(
      'https://example.com/collapsedhello',
    );
    expect(
      content.getEntity(content.getLastCreatedEntityKey()).getData().url,
    ).toBe('https://example.com/collapsed');
  });

  it('multiple plain-text links and emails', () => {
    const input =
      'http://a.co/ ftp://b.co/ test@example.com https://c.co/ ftps://d.co';
    const raw = testOnPasteOutput(input, null);
    expect(raw.blocks[0]).toMatchObject({
      text: `${input}hello`,
      entityRanges: [
        { offset: 0, length: 12, key: 0 },
        { offset: 13, length: 11, key: 1 },
        { offset: 25, length: 16, key: 2 },
        { offset: 42, length: 13, key: 3 },
        { offset: 56, length: 11, key: 4 },
      ],
    });
    expect(raw.entityMap).toMatchObject({
      0: {
        type: 'LINK',
        mutability: 'MUTABLE',
        data: { url: 'http://a.co/' },
      },
      1: { data: { url: 'ftp://b.co/' } },
      2: { data: { url: 'mailto:test@example.com' } },
      3: { data: { url: 'https://c.co/' } },
      4: { data: { url: 'ftps://d.co' } },
    });
  });

  it('multiple URLs and emails within HTML', () => {
    const input = `
    <p><span>start</span></p>
    <p><span>l1 http://a.co/</span></p>
    <p><span>l2a test@example.com l2b</span></p>
    <p><span>https://c.co/ l3</span></p>
    <p><span>end</span></p>
    `;
    const raw = testOnPasteOutput(input.replace(/<[^>]+/g), input);
    expect(raw.blocks).toMatchObject([
      { text: 'start', entityRanges: [] },
      {
        text: 'l1 http://a.co/',
        entityRanges: [{ offset: 3, length: 12, key: 0 }],
      },
      {
        text: 'l2a test@example.com l2b',
        entityRanges: [{ offset: 4, length: 16, key: 1 }],
      },
      {
        text: 'https://c.co/ l3',
        entityRanges: [{ offset: 0, length: 13, key: 2 }],
      },
      { text: 'endhello', entityRanges: [] },
    ]);
    expect(raw.entityMap).toMatchObject({
      0: { data: { url: 'http://a.co/' } },
      1: { data: { url: 'mailto:test@example.com' } },
      2: { data: { url: 'https://c.co/' } },
    });
  });

  it('preserves existing rich text', () => {
    const input = `
    <h2><span>Heading</span></h2>
    <p><span>http://a.co/</span></p>
    <p><span><a href="http://test.co/">link</a></span></p>
    `;
    const raw = testOnPasteOutput(input.replace(/<[^>]+/g), input);
    expect(raw.blocks).toMatchObject([
      { type: 'header-two', text: 'Heading', entityRanges: [] },
      {
        text: 'http://a.co/',
        entityRanges: [{ offset: 0, length: 12, key: 0 }],
      },
      { text: 'linkhello', entityRanges: [{ offset: 0, length: 4, key: 1 }] },
    ]);
    expect(raw.entityMap).toMatchObject({
      0: { data: { url: 'http://a.co/' } },
      1: { data: { url: 'http://test.co/' } },
    });
  });

  it('skips linking punctuation chars', () => {
    const punctuation = {
      // Characters that will be removed.
      '.': '',
      '?': '',
      '!': '',
      ':': '',
      ';': '',
      ',': '',
      // Syriac Harklean Metobelus
      '܌': '',
      '؟': '',
      '،': '',
      '‼': '',
      '﹒': '',
      // Characters that will be preserved.
      '…': '…',
      '-': '-',
      '_': '_',
      '–': '–',
      '+': '+',
      '=': '=',
    };
    const input = Object.keys(punctuation)
      .map((punc) => `<p><span>http://a.co/t${punc}/${punc}</span></p>`)
      .join(' ');
    const raw = testOnPasteOutput(input.replace(/<[^>]+/g), input);

    expect(raw.blocks.map(({ text }) => text)).toMatchSnapshot();
    expect(
      Object.values(raw.entityMap).map((entity) => entity.data.url),
    ).toMatchSnapshot();

    const expectedLength = Object.keys(punctuation).map(
      (punc) => `http://a.co/t${punc}/`.length + punctuation[punc].length,
    );
    expect(
      raw.blocks.map(({ entityRanges }) => entityRanges[0].length),
    ).toEqual(expectedLength);
  });
});

describe('pasted page link resolution', () => {
  let state;
  let editor;
  const entityType = {
    chooserUrls: { resolveLink: '/admin/choose-page/resolve-link/' },
  };
  const settle = () =>
    new Promise((resolve) => {
      setTimeout(resolve, 0);
    });
  const page = {
    id: 42,
    parentId: 2,
    url: '/about/',
    anchor: 'contact / café',
  };
  const currentLink = () => {
    const content = state.getCurrentContent();
    const key = content.getFirstBlock().getEntityAt(0);
    return key ? content.getEntity(key).getData() : null;
  };
  const paste = (url) => onPasteLink(url, null, state, editor, entityType);
  const deferLookup = () => {
    let complete;
    fetch.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          complete = (data = page) =>
            resolve({ status: 200, json: async () => data });
        }),
    );
    return (data) => complete(data);
  };

  beforeEach(() => {
    fetch.mockReset();
    state = EditorState.createWithContent(ContentState.createFromText('hello'));
    state = EditorState.forceSelection(
      state,
      state.getSelection().merge({ focusOffset: 5 }),
    );
    editor = {
      setEditorState: jest.fn((next) => {
        state = next;
      }),
      getEditorState: () => state,
    };
  });

  it('applies a URL immediately and resolves its page ID and fragment', async () => {
    fetch.mockResponseSuccessJSON(JSON.stringify(page));
    expect(paste('http://localhost/about/#contact%20%2F%20caf%C3%A9')).toBe(
      'handled',
    );
    expect(currentLink().url).toBe(
      'http://localhost/about/#contact%20%2F%20caf%C3%A9',
    );
    await settle();
    expect(currentLink()).toEqual({
      ...page,
      url: '/about/#contact%20%2F%20caf%C3%A9',
    });
    expect(state.getCurrentContent().getPlainText()).toBe('hello');
    expect(state.getUndoStack().size).toBe(1);
    const undone = EditorState.undo(state).getCurrentContent();
    expect(undone.getFirstBlock().getEntityAt(0)).toBeNull();
  });

  it('preserves typing and selection changes during resolution', async () => {
    const complete = deferLookup();
    paste('http://localhost/about/');
    const cursor = state
      .getSelection()
      .merge({ anchorOffset: 5, focusOffset: 5 });
    const content = Modifier.insertText(state.getCurrentContent(), cursor, '!');
    state = EditorState.push(state, content, 'insert-characters');
    state = EditorState.forceSelection(state, content.getSelectionAfter());
    const selection = state.getSelection();
    complete();
    await settle();
    expect(state.getCurrentContent().getPlainText()).toBe('hello!');
    expect(state.getSelection()).toBe(selection);
    expect(currentLink().id).toBe(42);
  });

  it('does not restore a link undone before resolution completes', async () => {
    const complete = deferLookup();
    paste('http://localhost/about/');
    state = EditorState.undo(state);
    const undone = state;
    complete();
    await settle();
    expect(state).toBe(undone);
    expect(currentLink()).toBeNull();
  });

  it('leaves an external URL unchanged', async () => {
    fetch.mockResponseSuccessJSON(
      JSON.stringify({ url: 'https://example.com/' }),
    );
    paste('https://example.com/');
    const pasted = state;
    await settle();
    expect(state).toBe(pasted);
    expect(currentLink()).toEqual({ url: 'https://example.com/' });
  });

  it('keeps the ordinary link when lookup fails', async () => {
    fetch.mockResponseCrash();
    paste('http://localhost/about/');
    const pasted = state;
    await settle();
    expect(state).toBe(pasted);
    expect(currentLink().url).toBe('http://localhost/about/');
  });

  it('handles fragment-only links without a lookup', () => {
    expect(paste('#contact')).toBe('handled');
    expect(currentLink()).toEqual({ url: '#contact' });
    expect(state.getCurrentContent().getPlainText()).toBe('hello');
    expect(fetch).not.toHaveBeenCalled();
  });

  it('resolves relative URLs', async () => {
    fetch.mockResponseSuccessJSON(JSON.stringify(page));
    expect(paste('/about/#contact')).toBe('handled');
    await settle();
    expect(currentLink().id).toBe(42);
  });
});
