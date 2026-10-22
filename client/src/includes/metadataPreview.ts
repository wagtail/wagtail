import { PageMetadata, getMetaTag } from './metadataExtraction';

/**
 * Approximation of the desktop Google Search title font, used for
 * pixel-length measurements of the `<title>`. Approximate on purpose:
 * Google truncates title links "as needed, typically to fit the device
 * width", with no documented limit. Community measurements converge on
 * a ~580px desktop display budget.
 */
export const TITLE_FONT = '20px Arial, Helvetica, sans-serif';
export const TITLE_BUDGET_PX = 580;

/**
 * Soft display budget for the title in search results, in characters.
 * Companion to the pixel budget above.
 */
export const TITLE_CHAR_BUDGET = 60;

/**
 * Soft display budget for the meta description in search results.
 * Google truncates snippets "as needed" with no documented limit; longer
 * descriptions provide no benefit, hence the display-only budget.
 */
export const DESCRIPTION_BUDGET_CHARS = 160;

/** Maximum length of meta tag contents displayed in the tag viewer. */
export const META_TAG_LIMIT = 100;

/**
 * The `rel` values of `link` tags that are relevant as page metadata, and
 * thus listed in the "View more meta tags" viewer. Based on the relations
 * documented on MDN, plus the `shortlink` and `amphtml` conventions widely
 * emitted by CMSs for SEO purposes. All other relations (stylesheets,
 * resource hints, icons, …) are page plumbing rather than metadata.
 * @see https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/rel
 */
const METADATA_LINK_RELS = new Set([
  'alternate',
  'amphtml',
  'canonical',
  'next',
  'prev',
  'shortlink',
]);

let measureCanvas: HTMLCanvasElement | null = null;

/**
 * Measure the rendered width of a string in pixels, using an offscreen
 * canvas at the desktop SERP font size. Returns 0 when the canvas API is
 * unavailable (e.g. test environments without canvas support).
 */
export const measureTextWidth = (text: string): number => {
  if (!measureCanvas) {
    measureCanvas = document.createElement('canvas');
  }
  const context = measureCanvas.getContext('2d');
  if (!context) return 0;
  context.font = TITLE_FONT;
  return context.measureText(text).width;
};

const truncateTagContent = (content: string) => {
  if (content.length <= META_TAG_LIMIT) return content;
  return `${content.slice(0, META_TAG_LIMIT - 1)}…`;
};

/**
 * Whether a `link` tag's `rel` value holds any metadata-relevant relation.
 * The rel attribute may hold multiple tokens ('alternate stylesheet').
 */
const hasMetadataRel = (rel: string): boolean =>
  rel
    .toLowerCase()
    .split(/\s+/)
    .some((value) => METADATA_LINK_RELS.has(value));

/**
 * Render the raw meta tag viewer: every `meta` tag (name/property → content)
 * and every `link` tag holding a metadata-relevant `rel` value (canonical,
 * alternate, shortlink, pagination, …).
 */
const renderTagViewer = (metadata: PageMetadata, root: ParentNode): void => {
  const container = root.querySelector('[data-metadata-tags]');
  if (!container) return;

  container.innerHTML = '';

  const addEntry = (key: string, value: string) => {
    const dt = document.createElement('dt');
    dt.textContent = key;
    const dd = document.createElement('dd');
    dd.textContent = truncateTagContent(value);
    if (value.length > META_TAG_LIMIT) {
      dd.title = value;
    }
    container.append(dt, dd);
  };

  metadata.metaTags.forEach((meta) => {
    addEntry(meta.name || meta.property || '', meta.content);
  });
  metadata.linkTags
    .filter((link) => hasMetadataRel(link.rel))
    .forEach((link) => {
      addEntry(link.rel, link.href);
    });
};

/**
 * Render the page's basic metadata into the "Page metadata" section slots of
 * the shared `wagtailadmin/shared/content_checks/metadata.html` template: the
 * title and description, with their lengths, and the raw meta tag viewer.
 * A no-op when metadata is unavailable.
 */
export const renderMetadataSection = (
  metadata: PageMetadata | null | undefined,
  root: ParentNode,
): void => {
  if (!metadata) return;

  const title = metadata.title;
  const description = getMetaTag(metadata.metaTags, 'description') || '';

  const titleSlot = root.querySelector('[data-metadata-title]');
  if (titleSlot) {
    titleSlot.textContent = title;
  }

  const titleLength = root.querySelector('[data-metadata-title-length]');
  if (titleLength) {
    const width = Math.round(measureTextWidth(title));
    titleLength.textContent =
      width > 0
        ? `${title.length}/${TITLE_CHAR_BUDGET} (${width}/${TITLE_BUDGET_PX} px)`
        : `${title.length}/${TITLE_CHAR_BUDGET}`;
  }

  // The description field is hidden altogether when the page has no
  // meta description tag, or when the tag is empty.
  const descriptionField = root.querySelector<HTMLElement>(
    '[data-metadata-description-field]',
  );
  if (descriptionField) {
    descriptionField.hidden = !description;
  }

  const descriptionSlot = root.querySelector('[data-metadata-description]');
  if (descriptionSlot) {
    descriptionSlot.textContent = description;
  }

  const descriptionChars = root.querySelector(
    '[data-metadata-description-chars]',
  );
  if (descriptionChars) {
    descriptionChars.textContent = `${description.length}/${DESCRIPTION_BUDGET_CHARS}`;
  }

  renderTagViewer(metadata, root);
};
