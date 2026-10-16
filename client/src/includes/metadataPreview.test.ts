import { PageMetadata } from './metadataExtraction';
import {
  TITLE_BUDGET_PX,
  TITLE_CHAR_BUDGET,
  TITLE_FONT,
  renderMetadataSection,
} from './metadataPreview';

/** Minimal DOM fixture matching the metadata.html markup shape. */
const metadataFixture = `
  <div data-metadata-section>
    <p data-metadata-title></p>
    <p data-metadata-title-length></p>
    <div data-metadata-description-field>
      <p data-metadata-description></p>
      <p data-metadata-description-chars></p>
    </div>
    <details data-metadata-tags-disclosure>
      <dl data-metadata-tags></dl>
    </details>
  </div>
`;

const fullMetadata: PageMetadata = {
  title: 'Page title',
  url: 'https://example.com/fr/bakery/',
  metaTags: [
    { name: 'description', content: 'Page description' },
    { property: 'og:title', content: 'OG title' },
  ],
  linkTags: [{ rel: 'canonical', href: 'https://example.com/canonical/' }],
  jsonLdScripts: [],
};

describe('renderMetadataSection', () => {
  beforeEach(() => {
    document.body.innerHTML = metadataFixture;
    const measureText = jest.fn((text: string) => ({
      width: text.length * 10,
    }));
    jest
      .spyOn(HTMLCanvasElement.prototype, 'getContext')
      .mockReturnValue({ measureText } as unknown as CanvasRenderingContext2D);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders the title and description with their lengths', () => {
    renderMetadataSection(fullMetadata, document);

    expect(
      document.querySelector('[data-metadata-title]')!.textContent,
    ).toEqual('Page title');
    // 10 chars, 10 chars * 10px = 100px
    expect(
      document.querySelector('[data-metadata-title-length]')!.textContent,
    ).toEqual(`10/${TITLE_CHAR_BUDGET} (100/${TITLE_BUDGET_PX} px)`);
    expect(
      document.querySelector('[data-metadata-description]')!.textContent,
    ).toEqual('Page description');
    expect(
      document.querySelector('[data-metadata-description-chars]')!.textContent,
    ).toEqual('16/160');
  });

  it('omits the pixel portion of the readout when pixels cannot be measured', () => {
    jest
      .spyOn(HTMLCanvasElement.prototype, 'getContext')
      .mockReturnValue(null as unknown as CanvasRenderingContext2D);

    renderMetadataSection(fullMetadata, document);

    expect(
      document.querySelector('[data-metadata-title-length]')!.textContent,
    ).toEqual(`10/${TITLE_CHAR_BUDGET}`);
  });

  it('hides the description field altogether when the tag is missing', () => {
    const metadata: PageMetadata = {
      ...fullMetadata,
      metaTags: [],
      linkTags: [],
    };

    renderMetadataSection(metadata, document);

    expect(
      document.querySelector<HTMLElement>('[data-metadata-description-field]')!
        .hidden,
    ).toEqual(true);
  });

  it('hides the description field when the tag exists but is empty', () => {
    const metadata: PageMetadata = {
      ...fullMetadata,
      metaTags: [{ name: 'description', content: '' }],
      linkTags: [],
    };

    renderMetadataSection(metadata, document);

    expect(
      document.querySelector<HTMLElement>('[data-metadata-description-field]')!
        .hidden,
    ).toEqual(true);
    expect(
      document.querySelector('[data-metadata-description]')!.textContent,
    ).toEqual('');
    expect(
      document.querySelector('[data-metadata-description-chars]')!.textContent,
    ).toEqual('0/160');
  });

  it('renders all meta tags except stylesheets in the viewer', () => {
    const longContent = 'x'.repeat(150);
    const metadata: PageMetadata = {
      ...fullMetadata,
      metaTags: [
        { property: 'og:title', content: 'First' },
        { property: 'og:title', content: longContent },
      ],
      linkTags: [
        { rel: 'canonical', href: 'https://example.com/canonical/' },
        { rel: 'stylesheet', href: '/static/style.css' },
      ],
    };

    renderMetadataSection(metadata, document);

    const tags = document.querySelector('[data-metadata-tags]')!;
    const terms = Array.from(tags.querySelectorAll('dt')).map(
      (dt) => dt.textContent,
    );
    const descriptions = Array.from(tags.querySelectorAll('dd')).map(
      (dd) => dd.textContent,
    );

    // Stylesheet links are page plumbing, not metadata – not listed.
    expect(terms).toEqual(['og:title', 'og:title', 'canonical']);
    expect(descriptions[0]).toEqual('First');
    // Long content is truncated for display, with the full value in title
    expect(descriptions[1]).toHaveLength(100 - 1 + 1);
    expect(descriptions[1]).not.toEqual(longContent);
    expect(tags.querySelectorAll('dd')[1].getAttribute('title')).toEqual(
      longContent,
    );
  });

  it('is a no-op when metadata is missing', () => {
    renderMetadataSection(null, document);

    expect(
      document.querySelector('[data-metadata-title]')!.textContent,
    ).toEqual('');
    renderMetadataSection(undefined, document);
    expect(
      document.querySelector('[data-metadata-title]')!.textContent,
    ).toEqual('');
  });
});

describe('constants', () => {
  it('defines the documented title budgets and font', () => {
    expect(TITLE_BUDGET_PX).toEqual(580);
    expect(TITLE_CHAR_BUDGET).toEqual(60);
    expect(TITLE_FONT).toEqual('20px Arial, Helvetica, sans-serif');
  });
});
