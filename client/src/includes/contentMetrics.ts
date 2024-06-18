interface ContentMetrics {
  wordCount: number;
  readingTime: number;
}

export const getWordCount = (lang: string, text: string): number => {
  const segmenter = new Intl.Segmenter(lang, { granularity: 'word' });
  const segments: Intl.SegmentData[] = Array.from(segmenter.segment(text));
  const wordCount = segments.reduce(
    (count, segment) => (segment.isWordLike ? count + 1 : count),
    0,
  );

  return wordCount;
};

/*
Language-specific reading speeds according to a meta-analysis of 190 studies on reading rates.
Study preprint: https://osf.io/preprints/psyarxiv/xynwg/
DOI: https://doi.org/10.1016/j.jml.2019.104047
 */
const readingSpeeds = {
  ar: 181, // Arabic
  zh: 260, // Chinese
  nl: 228, // Dutch
  en: 238, // English
  fi: 195, // Finnish
  fr: 214, // French
  de: 260, // German
  he: 224, // Hebrew
  it: 285, // Italian
  ko: 226, // Korean
  es: 278, // Spanish
  sv: 218, // Swedish
};

export const getReadingTime = (lang: string, wordCount: number): number => {
  const locale = lang.split('-')[0];
  // Fallback to English reading speed if the locale is not found
  const readingSpeed = readingSpeeds[locale] || readingSpeeds.en;
  const readingTime = Math.round(wordCount / readingSpeed);

  return readingTime;
};

const renderContentMetrics = ({ wordCount, readingTime }: ContentMetrics) => {
  const wordCountContainer = document.querySelector<HTMLElement>(
    '[data-content-word-count]',
  );
  const readingTimeContainer = document.querySelector<HTMLElement>(
    '[data-content-reading-time]',
  );
  const readingTimeSingleUnit = document.querySelector<HTMLElement>(
    '[data-content-reading-time-single]',
  );
  const readingTimeUnitPluralUnit = document.querySelector<HTMLElement>(
    '[data-content-reading-time-plural]',
  );

  if (
    !wordCountContainer ||
    !readingTimeContainer ||
    !readingTimeSingleUnit ||
    !readingTimeUnitPluralUnit
  )
    return;

  if (readingTime === 1) {
    readingTimeSingleUnit.hidden = false;
    readingTimeUnitPluralUnit.hidden = true;
  }
  wordCountContainer.textContent = wordCount.toString();
  readingTimeContainer.textContent = readingTime.toString();
};

export const runContentCheck = () => {
  const iframe = document.querySelector<HTMLIFrameElement>(
    '[data-preview-iframe]',
  );
  const iframeDocument =
    iframe?.contentDocument || iframe?.contentWindow?.document;
  const text = iframeDocument?.querySelector('main')?.innerText;
  if (!iframe || !iframeDocument || !text) {
    return;
  }
  const lang = iframeDocument.documentElement.lang || 'en';

  const wordCount = getWordCount(lang, text);
  const readingTime = getReadingTime(lang, wordCount);

  renderContentMetrics({ wordCount, readingTime });
};
