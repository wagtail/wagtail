import {
  getWordCount,
  getReadingTime,
  getLIXScore,
  getReadabilityScore,
  contentExtractorPluginInstance,
} from './contentMetrics';

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

describe.each`
  text                                                                             | lang    | lix
  ${'Hello world less than 10 words.'}                                             | ${'en'} | ${0}
  ${'This is a simple one just over 10 words in length.'}                          | ${'en'} | ${11}
  ${'This is a longer and more complicated sentence including long words.'}        | ${'en'} | ${38.27}
  ${'A sentence conceived specially as to contain particularly extended wording.'} | ${'en'} | ${80}
  ${'Ceci est une phrase simple avec juste au dessus de 10 mots.'}                 | ${'fr'} | ${12}
  ${'이 문장은 열한 단어보다 조금 더 긴 아주 간단한 문장입니다.'}                  | ${'ko'} | ${10}
  ${'המשפט הזה הוא משפט פשוט מאוד, קצת יותר מאחד־עשר מילים.'}                      | ${'he'} | ${11}
  ${'这个句子非常简单，不过比十一个词稍微长一点。'}                                | ${'zh'} | ${12}
  ${'هذه الجملة بسيطة جدًا، لكنها أطول قليلًا من إحدى عشرة كلمة.'}                 | ${'ar'} | ${11}
  ${''}                                                                            | ${'en'} | ${0}
  ${'No punctuation'}                                                              | ${'en'} | ${0}
`('getLIXScore', ({ text, lang, lix }) => {
  test(`LIX score for '${text}' in language '${lang}'`, () => {
    expect(getLIXScore(lang, text)).toBeCloseTo(lix);
  });
});

describe.each`
  lix   | readability
  ${0}  | ${'Good'}
  ${11} | ${'Good'}
  ${38} | ${'Fair'}
  ${80} | ${'Complex'}
`('getReadabilityScore', ({ lix, readability }) => {
  test(`readability score for LIX '${lix}'`, () => {
    expect(getReadabilityScore(lix)).toBe(readability);
  });
});

describe('contentExtractorPluginInstance', () => {
  let originalInnerText;
  beforeAll(() => {
    originalInnerText = Object.getOwnPropertyDescriptor(
      HTMLElement.prototype,
      'innerText',
    );
  });

  beforeEach(() => {
    document.body.innerHTML = `
      <main>
        <p>Test content</p>
      </main>
      <div>Something else</div>
    `;

    // innerText is not implemented in JSDOM
    // https://github.com/jsdom/jsdom/issues/1245
    Object.defineProperty(HTMLElement.prototype, 'innerText', {
      configurable: true,
      get() {
        return this.textContent;
      },
    });
  });

  afterAll(() => {
    Object.defineProperty(HTMLElement.prototype, 'innerText', {
      configurable: true,
      value: originalInnerText,
    });
  });

  it('should use the specified selector', () => {
    const done = jest.fn();
    contentExtractorPluginInstance.extract({ targetElement: 'main' }, done);
    expect(done).toHaveBeenCalledTimes(1);
    const content = done.mock.lastCall[0];
    expect(content.lang).toEqual('en');
    expect(content.innerText.trim()).toEqual('Test content');
    expect(content.innerHTML.trim()).toEqual('<p>Test content</p>');
  });

  it('should fall back to the body element if the selector does not match any elements', () => {
    const done = jest.fn();
    contentExtractorPluginInstance.extract({ targetElement: 'article' }, done);
    expect(done).toHaveBeenCalledTimes(1);
    const content = done.mock.lastCall[0];
    expect(content.lang).toEqual('en');
    expect(content.innerText.trim().replace(/\s+/g, ' ')).toEqual(
      'Test content Something else',
    );
    expect(content.innerHTML.trim().replace(/\s+/g, ' ')).toEqual(
      '<main> <p>Test content</p> </main> <div>Something else</div>',
    );
  });
});
