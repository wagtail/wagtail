import {
  type ExtractedContent,
  contentExtractorPluginInstance,
  getLIXScore,
  getReadabilityScore,
  getReadingTime,
  getWordCount,
  registerMetric,
  renderContentMetrics,
  resetMetrics,
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

  it('should include the document head metadata', () => {
    document.head.innerHTML = `
      <title>Test page</title>
      <meta name="description" content="Test description">
    `;
    const done = jest.fn();
    contentExtractorPluginInstance.extract({ targetElement: 'main' }, done);
    const content = done.mock.lastCall[0];
    expect(content.metadata.title).toEqual('Test page');
    expect(content.metadata.metaTags).toEqual([
      { name: 'description', content: 'Test description' },
    ]);
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

describe('renderContentMetrics', () => {
  // innerText is not implemented in JSDOM
  // https://github.com/jsdom/jsdom/issues/1245
  beforeAll(() => {
    Object.defineProperty(HTMLElement.prototype, 'innerText', {
      configurable: true,
      get() {
        return this.textContent;
      },
    });
  });

  afterAll(() => {
    delete (HTMLElement.prototype as any).innerText;
  });

  const buildRoot = () => {
    const root = document.createElement('div');
    root.innerHTML = `
      <div data-metric-list></div>
      <p data-metric-value="word-count"></p>
      <p data-metric-value="reading-time"></p>
      <p data-metric-value="readability-score"></p>
    `;
    return root;
  };

  const extractedContent = () => {
    document.body.innerHTML = `
      <main><p>${'word '.repeat(238)}</p></main>
    `;
    let content: ExtractedContent;
    contentExtractorPluginInstance.extract(
      { targetElement: 'main' },
      (result) => {
        content = result;
      },
    );
    return content!;
  };

  afterEach(() => {
    document.body.innerHTML = '';
    resetMetrics();
  });

  it('renders every metric definition into slots within the given root', () => {
    const root = buildRoot();
    const content = extractedContent();

    renderContentMetrics(content, root);

    const slots = Object.fromEntries(
      Array.from(root.querySelectorAll('[data-metric-value]')).map((slot) => [
        slot.getAttribute('data-metric-value'),
        slot.textContent,
      ]),
    );
    expect(slots['word-count']).toEqual('238');
    expect(slots['reading-time']).toEqual('1 min');
    expect(slots['readability-score']).toBeTruthy();
  });

  it('renders registered metrics as extra rows', () => {
    const root = buildRoot();
    registerMetric({
      id: 'text-ratio',
      getLabel: () => 'Text ratio',
      compute: () => '12%',
    });
    const content = extractedContent();

    renderContentMetrics(content, root);

    const list = root.querySelector('[data-metric-list]')!;
    expect(list.textContent).toContain('Text ratio');
    expect(list.textContent).toContain('12%');
  });

  it('handles missing slots gracefully', () => {
    const root = document.createElement('div');
    const content = extractedContent();

    expect(() => renderContentMetrics(content, root)).not.toThrow();
  });

  it('uses the document as the fallback root', () => {
    const content = extractedContent();
    document.body.innerHTML = `
      <div data-metric-list></div>
      <p data-metric-value="word-count"></p>
    `;

    renderContentMetrics(content);

    expect(
      document.querySelector('[data-metric-value="word-count"]')!.textContent,
    ).toEqual('238');
  });
});

describe('renderContentMetrics repeated rendering', () => {
  beforeAll(() => {
    Object.defineProperty(HTMLElement.prototype, 'innerText', {
      configurable: true,
      get() {
        return this.textContent;
      },
    });
  });

  afterAll(() => {
    delete (HTMLElement.prototype as any).innerText;
  });

  afterEach(() => {
    document.body.innerHTML = '';
    resetMetrics();
  });

  it('does not duplicate registered metric rows when re-rendered', () => {
    registerMetric({
      id: 'text-ratio',
      getLabel: () => 'Text ratio',
      compute: () => '12%',
    });
    document.body.innerHTML = `
      <main><p>${'word '.repeat(238)}</p></main>
    `;
    let content: ExtractedContent;
    contentExtractorPluginInstance.extract(
      { targetElement: 'main' },
      (result) => {
        content = result;
      },
    );
    const root = document.createElement('div');
    root.innerHTML = `
      <div data-metric-list></div>
      <p data-metric-value="word-count"></p>
    `;

    renderContentMetrics(content!, root);
    renderContentMetrics(content!, root);
    renderContentMetrics(content!, root);

    const rows = root.querySelectorAll('[data-registered-metric]');
    expect(rows).toHaveLength(1);
    expect(root.textContent!.match(/Text ratio/g)).toHaveLength(1);
  });
});
