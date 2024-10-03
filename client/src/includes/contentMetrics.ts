import axe from 'axe-core';
import { ngettext } from '../utils/gettext';

export const getWordCount = (lang: string, text: string): number => {
  // Firefox ESR doesn’t have support for Intl.Segmenter yet.
  if (typeof Intl.Segmenter === 'undefined') {
    return 0;
  }

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

interface ContentMetricsOptions {
  targetElement: string;
}

interface ContentMetrics {
  wordCount: number;
  readingTime: number;
}

export const contentMetricsPluginInstance = {
  id: 'metrics',
  getMetrics(
    options: ContentMetricsOptions,
    done: (metrics: ContentMetrics) => void,
  ) {
    const main =
      document.querySelector<HTMLElement>(options.targetElement) ||
      document.body; // Fallback to the body only if the target element is not found
    const text = main?.innerText || '';
    const lang = document.documentElement.lang || 'en';
    const wordCount = getWordCount(lang, text);
    const readingTime = getReadingTime(lang, wordCount);
    done({
      wordCount,
      readingTime,
    });
  },
};

/**
 * Calls the `getMetrics` method in the `metrics` plugin instance of the `wagtailPreview` registry.
 * Wrapped in a promise so we can use async/await syntax instead of callbacks
 */
export const getPreviewContentMetrics = (
  options: ContentMetricsOptions,
): Promise<ContentMetrics> =>
  new Promise((resolve) => {
    axe.plugins.wagtailPreview.run(
      'metrics',
      'getMetrics',
      options,
      (metrics: ContentMetrics) => {
        resolve(metrics);
      },
    );
  });

export const renderContentMetrics = ({
  wordCount,
  readingTime,
}: ContentMetrics) => {
  // Skip updates if word count isn’t set.
  if (!wordCount) {
    return;
  }

  const wordCountContainer = document.querySelector<HTMLElement>(
    '[data-content-word-count]',
  );
  const readingTimeContainer = document.querySelector<HTMLElement>(
    '[data-content-reading-time]',
  );

  if (!wordCountContainer || !readingTimeContainer) return;

  wordCountContainer.textContent = wordCount.toString();
  readingTimeContainer.textContent = ngettext(
    '%(num)s min',
    '%(num)s mins',
    readingTime,
  ).replace('%(num)s', `${readingTime}`);
};
