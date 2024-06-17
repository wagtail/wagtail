interface ContentMetrics {
  wordCount: number;
  readingTime: number;
}

interface SegmentData {
  segment: string;
  isWordLike?: boolean | undefined;
}

export const getContentMetrics = (
  lang: string,
  text: string,
): ContentMetrics => {
  let wordCount = 0;

  if (typeof Intl.Segmenter === 'function') {
    const segmenter = new Intl.Segmenter(lang, { granularity: 'word' });
    const segments: SegmentData[] = Array.from(segmenter.segment(text));
    wordCount = segments.reduce(
      (count, segment) => (segment.isWordLike ? count + 1 : count),
      0,
    );
  } else {
    // Fallback to regex if Intl.Segmenter is not supported
    wordCount =
      text
        .trim()
        .replace(/['";:,.?¿\-!¡]+/g, '')
        .match(/\S+/g)?.length || 0;
  }

  // Silent-reading adults average 238 words per minute
  const readingTime = Math.round(wordCount / 238);

  return {
    wordCount,
    readingTime,
  };
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
  const lang = iframeDocument.documentElement.lang || 'en-US';
  const contentMetrics = getContentMetrics(lang, text);

  renderContentMetrics(contentMetrics);
};
