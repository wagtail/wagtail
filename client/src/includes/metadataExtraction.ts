export interface MetaTagData {
  name?: string;
  property?: string;
  content: string;
}

export interface LinkTagData {
  rel: string;
  href: string;
  hreflang?: string;
  type?: string;
}

export interface PageMetadata {
  /** The `<title>` text, untruncated. */
  title: string;
  /** The document's URL, used as the base for resolving relative URLs. */
  url: string;
  /** Every `<meta>` tag with a `name` or `property` attribute and a `content` attribute. */
  metaTags: MetaTagData[];
  /** Every `<link>` tag with a `rel` attribute (canonical, alternate, etc.). */
  linkTags: LinkTagData[];
  /** Raw text of every `<script type="application/ld+json">`, in document order. */
  jsonLdScripts: string[];
}

/**
 * Get the content of the first `<meta>` tag matching `name` or `property`,
 * case-insensitively. Duplicate tags are common – the first one wins,
 * mirroring common platform behaviour.
 */
export const getMetaTag = (
  metaTags: MetaTagData[],
  key: string,
): string | undefined => {
  const needle = key.toLowerCase();
  const tag = metaTags.find(
    (meta) =>
      meta.name?.toLowerCase() === needle ||
      meta.property?.toLowerCase() === needle,
  );
  return tag?.content;
};

/**
 * Extract SEO / social media metadata from a document's head:
 * the `<title>`, all `<meta>` tags with a `name` or `property` attribute,
 * all `<link>` tags with a `rel` attribute, and raw JSON-LD script contents.
 */
export const getPageMetadata = (doc: Document): PageMetadata => ({
  title: doc.title || '',
  url: doc.URL,
  metaTags: Array.from(
    doc.head.querySelectorAll<HTMLMetaElement>(
      'meta[name][content], meta[property][content]',
    ),
  ).map((meta) => ({
    ...(meta.getAttribute('name') && { name: meta.getAttribute('name')! }),
    ...(meta.getAttribute('property') && {
      property: meta.getAttribute('property')!,
    }),
    content: meta.getAttribute('content')!,
  })),
  linkTags: Array.from(
    doc.head.querySelectorAll<HTMLLinkElement>('link[rel][href]'),
  ).map((link) => ({
    rel: link.getAttribute('rel')!,
    href: link.getAttribute('href')!,
    ...(link.getAttribute('hreflang') && {
      hreflang: link.getAttribute('hreflang')!,
    }),
    ...(link.getAttribute('type') && { type: link.getAttribute('type')! }),
  })),
  jsonLdScripts: Array.from(
    doc.head.querySelectorAll<HTMLScriptElement>(
      'script[type="application/ld+json"]',
    ),
  ).map((script) => script.textContent || ''),
});
