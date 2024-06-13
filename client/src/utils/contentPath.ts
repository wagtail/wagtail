export function getContentPathSelector(contentPath?: string) {
  let path = contentPath;
  if (!path) {
    const contentPathPrefix = '#w-content-path:';
    if (!window.location.hash.startsWith(contentPathPrefix)) return '';

    path = window.location.hash.slice(contentPathPrefix.length);
  }

  const pathFragments = path.split('.');
  const selector = pathFragments.reduce((acc, fragment) => {
    if (acc) {
      // In some cases the fragment can be empty, e.g. when the path ends with
      // a trailing dot, which may be the case with inline panels.
      return fragment ? `${acc} [data-contentpath="${fragment}"]` : acc;
    }
    return `[data-contentpath="${fragment}"]`;
  }, '');
  return selector;
}
