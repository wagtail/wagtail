import React from 'react';
import { shallow } from 'enzyme';
import { EditorState, convertFromRaw, RawDraftContentState } from 'draft-js';

import MaxLength, { countCharacters, getPlainText } from './MaxLength';

/**
 * Keep those tests up-to-date with RichTextMaxLengthValidator tests server-side.
 */
describe('MaxLength', () => {
  it('works', () => {
    const contentState = convertFromRaw({
      entityMap: {},
      blocks: [{ text: 'hello' }],
    } as RawDraftContentState);
    const editorState = EditorState.createWithContent(contentState);

    expect(
      shallow(
        <MaxLength
          getEditorState={() => editorState}
          onChange={() => {}}
          id="max-length-test"
          maxLength={10}
        />,
      ).text(),
    ).toBe('Character count:5/10');
  });

  it('supports 0', () => {
    expect(
      shallow(
        <MaxLength
          getEditorState={() => EditorState.createEmpty()}
          onChange={() => {}}
          id="max-length-test"
          maxLength={10}
        />,
      ).text(),
    ).toBe('Character count:0/10');
  });

  it('ignores atomic blocks', () => {
    const contentState = convertFromRaw({
      entityMap: {},
      blocks: [
        { text: 'hello' },
        { text: ' ', type: 'atomic' },
        { text: 'world' },
      ],
    } as RawDraftContentState);
    const editorState = EditorState.createWithContent(contentState);

    expect(
      shallow(
        <MaxLength
          getEditorState={() => editorState}
          onChange={() => {}}
          id="max-length-test"
          maxLength={10}
        />,
      ).text(),
    ).toBe('Character count:10/10');
  });
});

// Make sure count here matches result in TestRichTextLengthValidators.test_count_characters
test.each([
  // Embed blocks should be ignored.
  [['Plain text'], 'Plain text', 10],
  // HTML entities should be un-escaped.
  [["There's quote"], "There's quote", 13],
  // BR should be ignored.
  [['Line\nbreak'], 'Linebreak', 9],
  // Content over multiple blocks should be treated as a single line of text with no joiner.
  [['Multi', 'blocks'], 'Multiblocks', 11],
  // Empty blocks should be ignored.
  [['Empty', '', 'blocks'], 'Emptyblocks', 11],
])('getPlainText', (blocks, plainText, count) => {
  const contentState = convertFromRaw({
    entityMap: {},
    blocks: blocks.map((block) => ({ text: block })),
  } as RawDraftContentState);
  const editorState = EditorState.createWithContent(contentState);
  const text = getPlainText(editorState);
  // Check the plain-text version as well to help with troubleshooting.
  expect(text).toBe(plainText);
  expect(countCharacters(text)).toBe(count);
});

// Make sure count here matches result in TestRichTextLengthValidators.test_count_characters
describe.each`
  text         | result | segmenterLength
  ${'123456'}  | ${6}   | ${6}
  ${'123 45'}  | ${6}   | ${6}
  ${'123\n45'} | ${6}   | ${6}
  ${'\n'}      | ${1}   | ${1}
  ${''}        | ${0}   | ${0}
  ${' '}       | ${1}   | ${1}
  ${'❤️'}      | ${2}   | ${1}
  ${'👨‍👨‍👧'}      | ${5}   | ${1}
`('countCharacters', ({ text, result, segmenterLength }) => {
  test(text, () => {
    expect(countCharacters(text)).toBe(result);
    // For debugging only – show the segmenter grapheme length as a reference of the perceived length.
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore
    const seg = new Intl.Segmenter('en', { granularity: 'grapheme' });
    expect(Array.from(seg.segment(text))).toHaveLength(segmenterLength);
  });
});
