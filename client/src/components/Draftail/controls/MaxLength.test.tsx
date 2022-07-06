import React from 'react';
import { shallow } from 'enzyme';
import { EditorState, convertFromHTML, ContentState } from 'draft-js';

import MaxLength, { countCharacters } from './MaxLength';

describe('MaxLength', () => {
  it('works', () => {
    const { contentBlocks } = convertFromHTML('<p>hello</p>');
    const contentState = ContentState.createFromBlockArray(contentBlocks);
    const editorState = EditorState.createWithContent(contentState);

    expect(
      shallow(
        <MaxLength getEditorState={() => editorState} onChange={() => {}} />,
      ),
    ).toMatchInlineSnapshot(`
      <div
        className="w-inline-block w-tabular-nums w-label-3"
      >
        <span
          className="w-sr-only"
        >
          Character count:
        </span>
        <span>
          5
        </span>
      </div>
    `);
  });

  it('supports 0', () => {
    expect(
      shallow(
        <MaxLength
          getEditorState={() => EditorState.createEmpty()}
          onChange={() => {}}
        />,
      ),
    ).toMatchInlineSnapshot(`
      <div
        className="w-inline-block w-tabular-nums w-label-3"
      >
        <span
          className="w-sr-only"
        >
          Character count:
        </span>
        <span>
          0
        </span>
      </div>
    `);
  });
});

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
