const WAGTAIL_DIRECTIVE_DELIMITER = ':w:';

/**
 * Extract the Wagtail directives from the URL fragment.
 *
 * This follows the algorithm described in
 * https://wicg.github.io/scroll-to-text-fragment/#extracting-the-fragment-directive
 * for extracting the fragment directive from the URL fragment, with a few
 * differences:
 * - We use a :w: delimiter instead of the proposed :~: delimiter.
 * - We don't remove our directive from the URL fragment.
 *
 * @param rawFragment The raw fragment (hash) from the URL,
 * @returns a string of Wagtail directives, if any, in the style of URL search parameters.
 *
 * @example window.location.hash = '#:w:contentpath=abc1.d2e.3f'
 * // getWagtailDirectives() === 'contentpath=abc1.d2e.3f'
 *
 * @example window.location.hash = '#an-anchor:w:contentpath=abc1.d2e.3f'
 * // getWagtailDirectives() === 'contentpath=abc1.d2e.3f'
 *
 * @example window.location.hash = '#hello:w:contentpath=abc1.d2e.3f&unknown=123&unknown=456'
 * // getWagtailDirectives() === 'contentpath=abc1.d2e.3f&unknown=123&unknown=456'
 */
export function getWagtailDirectives() {
  const rawFragment = window.location.hash;
  const position = rawFragment.indexOf(WAGTAIL_DIRECTIVE_DELIMITER);
  if (position === -1) return '';
  return rawFragment.slice(position + WAGTAIL_DIRECTIVE_DELIMITER.length);
}

/**
 * Compose a selector string to find the content element based on the dotted
 * content path.
 *
 * @param contentPath dotted path to the content element.
 * @returns a selector string to find the content element.
 *
 * @example getContentPathSelector('abc1.d2e.3f')
 * // returns '[data-contentpath="abc1"] [data-contentpath="d2e"] [data-contentpath="3f"]'
 */
export function getContentPathSelector(contentPath: string) {
  const pathSegments = contentPath.split('.');
  const selector = pathSegments.reduce((acc, segment) => {
    // In some cases the segment can be empty, e.g. when the path ends with
    // a trailing dot, which may be the case with inline panels.
    if (!segment) return acc;

    const segmentSelector = `[data-contentpath="${segment}"]`;
    return acc ? `${acc} ${segmentSelector}` : segmentSelector;
  }, '');
  return selector;
}

/**
 * Get the content element based on a given content path (or one extracted from
 * the URL hash fragment).
 *
 * @param contentPath (optional) content path to the content element. If not
 * provided, it will be extracted from the URL fragment.
 * @returns the content element, if found, otherwise `null`.
 *
 * @example getElementByContentPath('abc1.d2e.3f')
 * // returns <div data-contentpath="3f">...</div>
 *
 * @example getElementByContentPath()
 * // with an URL e.g. https://example.com/#:w:contentpath=abc1.d2e.3f
 * // returns <div data-contentpath="3f">...</div>
 */
export function getElementByContentPath(contentPath?: string) {
  const path =
    contentPath ||
    new URLSearchParams(getWagtailDirectives()).get('contentpath');

  return path
    ? document.querySelector<HTMLElement>(getContentPathSelector(path))
    : null;
}
