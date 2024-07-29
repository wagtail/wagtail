import { getWordCount, getReadingTime } from './contentMetrics';

describe.each`
  text                                               | lang         | wordCount
  ${'¿Donde esta la biblioteca?'}                    | ${'es'}      | ${4}
  ${"It's lots. Of; Punctuation"}                    | ${'en'}      | ${4}
  ${'האהבה היא אוקיינוס שאין לו התחלה ואין לו סוף.'} | ${'he'}      | ${9}
  ${'元気です、ありがとう。あなたは？'}              | ${'zh'}      | ${5}
  ${'Dit is een testzin in het Nederlands.'}         | ${'nl'}      | ${7}
  ${'Je suis content de te voir!'}                   | ${'fr'}      | ${6}
  ${'Ich liebe dich!'}                               | ${'de'}      | ${3}
  ${'Mi piace molto questo libro.'}                  | ${'it'}      | ${5}
  ${'저는 오늘 날씨가 좋아요.'}                      | ${'ko'}      | ${4}
  ${'Unknown language code still works'}             | ${'invalid'} | ${5}
`('getWordCount', ({ text, lang, wordCount }) => {
  test(`correctly counts words in '${text}' for language '${lang}'`, () => {
    expect(getWordCount(lang, text)).toBe(wordCount);
  });
});

describe.each`
  lang         | wordCount | readingTime
  ${'es'}      | ${1000}   | ${4}
  ${'fr'}      | ${1000}   | ${5}
  ${'ar'}      | ${360}    | ${2}
  ${'it'}      | ${360}    | ${1}
  ${'en'}      | ${238}    | ${1}
  ${'en-us'}   | ${238}    | ${1}
  ${'he'}      | ${224}    | ${1}
  ${'zh'}      | ${520}    | ${2}
  ${'zh-Hans'} | ${520}    | ${2}
  ${'nl'}      | ${320}    | ${1}
  ${'ko'}      | ${50}     | ${0}
  ${'invalid'} | ${1000}   | ${4}
  ${''}        | ${1000}   | ${4}
`('getReadingTime', ({ lang, wordCount, readingTime }) => {
  test(`calculates reading time for '${wordCount}' words in language '${lang}'`, () => {
    expect(getReadingTime(lang, wordCount)).toBe(readingTime);
  });
});
