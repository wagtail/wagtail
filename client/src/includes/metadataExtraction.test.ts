import { getMetaTag, getPageMetadata } from './metadataExtraction';

describe('getPageMetadata', () => {
  it('extracts the title and document URL', () => {
    document.head.innerHTML = '<title>Home — Bakery</title>';

    const metadata = getPageMetadata(document);

    expect(metadata.title).toEqual('Home — Bakery');
    expect(metadata.url).toEqual(window.location.href);
  });

  it('collects meta tags with name or property and a content attribute', () => {
    document.head.innerHTML = `
      <meta charset="utf-8">
      <meta name="description" content="x">
      <meta property="og:title" content="y">
      <meta name="viewport">
    `;

    const metadata = getPageMetadata(document);

    expect(metadata.metaTags).toEqual([
      { name: 'description', content: 'x' },
      { property: 'og:title', content: 'y' },
    ]);
  });

  it('collects link tags with rel and href, keeping extra attributes', () => {
    document.head.innerHTML = `
      <link rel="canonical" href="https://example.com/">
      <link rel="alternate" hreflang="fr" href="https://example.com/fr/">
      <link href="https://example.com/no-rel/">
    `;

    const metadata = getPageMetadata(document);

    expect(metadata.linkTags).toEqual([
      { rel: 'canonical', href: 'https://example.com/' },
      { rel: 'alternate', href: 'https://example.com/fr/', hreflang: 'fr' },
    ]);
  });

  it('captures JSON-LD script text', () => {
    document.head.innerHTML = `
      <script type="application/ld+json">{"@type":"Organization"}</script>
      <script>console.log('not json-ld')</script>
      <script type="application/ld+json">{"@type":"WebSite"}</script>
    `;

    const metadata = getPageMetadata(document);

    expect(metadata.jsonLdScripts).toEqual([
      '{"@type":"Organization"}',
      '{"@type":"WebSite"}',
    ]);
  });

  it('returns empty collections on an empty head', () => {
    document.head.innerHTML = '';

    const metadata = getPageMetadata(document);

    expect(metadata.title).toEqual('');
    expect(metadata.url).toEqual(window.location.href);
    expect(metadata.metaTags).toEqual([]);
    expect(metadata.linkTags).toEqual([]);
    expect(metadata.jsonLdScripts).toEqual([]);
  });
});

describe('getMetaTag', () => {
  const metaTags = [
    { name: 'description', content: 'first' },
    { property: 'og:title', content: 'A' },
    { property: 'og:title', content: 'B' },
  ];

  it('returns the first matching tag by name or property', () => {
    expect(getMetaTag(metaTags, 'description')).toEqual('first');
    expect(getMetaTag(metaTags, 'og:title')).toEqual('A');
  });

  it('returns undefined for a missing tag', () => {
    expect(getMetaTag(metaTags, 'og:image')).toBeUndefined();
  });
});
