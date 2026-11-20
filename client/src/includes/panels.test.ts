import { initCollapsiblePanels, toggleCollapsiblePanel } from './panels';

const storageKey = 'wagtail:panel-expanded';

const renderPanels = (collapsed = false, content = '') => {
  document.body.innerHTML = ['body', 'related']
    .map(
      (id) => `
    <section data-panel class="${collapsed ? 'collapsed' : ''}">
      <button type="button" data-panel-toggle aria-controls="${id}" aria-expanded="true"></button>
      <h2 data-panel-heading>${id}</h2>
      <div id="${id}">${content}</div>
    </section>
  `,
    )
    .join('');
  initCollapsiblePanels();
  return Array.from(
    document.querySelectorAll<HTMLButtonElement>('[data-panel-toggle]'),
  );
};

const expectExpanded = (toggle: HTMLButtonElement, expanded: boolean) => {
  expect(toggle.getAttribute('aria-expanded')).toBe(String(expanded));
  expect(
    document
      .getElementById(toggle.getAttribute('aria-controls')!)!
      .hasAttribute('hidden'),
  ).toBe(!expanded);
};

describe('persistent collapsible panels', () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/admin/pages/2/edit/');
    localStorage.clear();
  });

  afterEach(() => {
    jest.restoreAllMocks();
    localStorage.clear();
    document.body.innerHTML = '';
    window.history.replaceState({}, '', '/');
  });

  it('restores collapsed panels without changing other panels', () => {
    const [body] = renderPanels();
    body.click();

    const [restoredBody, related] = renderPanels();
    expectExpanded(restoredBody, false);
    expectExpanded(related, true);
  });

  it('remembers expanding a panel that is collapsed by default', () => {
    const [body] = renderPanels(true);
    expectExpanded(body, false);
    body.click();

    const [restoredBody, related] = renderPanels(true);
    expectExpanded(restoredBody, true);
    expectExpanded(related, false);
  });

  it('keeps preferences separate by pathname, ignoring query strings', () => {
    const [pageBody] = renderPanels();
    pageBody.click();

    window.history.replaceState({}, '', '/admin/snippets/tests/advert/edit/2/');
    const [snippetBody, snippetRelated] = renderPanels();
    expectExpanded(snippetBody, true);
    snippetRelated.click();

    window.history.replaceState({}, '', '/admin/pages/2/edit/?next=/admin/');
    const [restoredBody, related] = renderPanels();
    expectExpanded(restoredBody, false);
    expectExpanded(related, true);

    window.history.replaceState({}, '', '/admin/snippets/tests/advert/edit/2/');
    const [restoredSnippetBody, restoredSnippetRelated] = renderPanels();
    expectExpanded(restoredSnippetBody, true);
    expectExpanded(restoredSnippetRelated, false);
  });

  it.each([
    '<input aria-invalid="true">',
    '<div class="error">Invalid</div>',
    '<div class="w-field--error">Invalid</div>',
  ])('reveals validation errors despite the saved state: %s', (error) => {
    const [body] = renderPanels();
    body.click();

    const [invalidBody] = renderPanels(false, error);
    expectExpanded(invalidBody, true);

    // Merely rendering an invalid form must not overwrite the preference.
    const [validBody] = renderPanels();
    expectExpanded(validBody, false);
  });

  it('remembers programmatic expansion, including browser find-in-page', () => {
    const [body] = renderPanels();
    toggleCollapsiblePanel(body, false);
    const [collapsedBody] = renderPanels();
    expectExpanded(collapsedBody, false);
    document.getElementById('body')!.dispatchEvent(new Event('beforematch'));

    const [restoredBody] = renderPanels();
    expectExpanded(restoredBody, true);
  });

  it('merges changes with preferences written by another tab', () => {
    const [body] = renderPanels();
    localStorage.setItem(
      storageKey,
      JSON.stringify({
        '/admin/pages/2/edit/': { related: false },
        '/admin/pages/3/edit/': { body: false },
      }),
    );
    body.click();

    const [restoredBody, related] = renderPanels();
    expectExpanded(restoredBody, false);
    expectExpanded(related, false);
    window.history.replaceState({}, '', '/admin/pages/3/edit/');
    const [otherBody] = renderPanels();
    expectExpanded(otherBody, false);
  });

  it.each(['invalid JSON', 'null'])(
    'recovers from invalid stored state: %s',
    (state) => {
      localStorage.setItem(storageKey, state);
      const [body] = renderPanels();
      expectExpanded(body, true);
      body.click();
      const [restoredBody] = renderPanels();
      expectExpanded(restoredBody, false);
    },
  );

  it('keeps panels usable when storage cannot be read or written', () => {
    jest.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new DOMException('Storage blocked', 'SecurityError');
    });
    jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new DOMException('Storage full', 'QuotaExceededError');
    });
    const [body] = renderPanels(true);
    expectExpanded(body, false);
    body.click();
    expectExpanded(body, true);
    body.click();
    expectExpanded(body, false);
  });
});
