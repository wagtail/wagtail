import initCollapsibleBreadcrumbs from './breadcrumbs';

describe('initCollapsibleBreadcrumbs', () => {
  const spy = jest.spyOn(document, 'addEventListener');

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should do nothing if there is no breadcrumbs container', () => {
    // Set up our document body
    document.body.innerHTML = `
    <div>
      <span id="username" />
      <button id="button" />
    </div>`;
    initCollapsibleBreadcrumbs();
    // no event listeners registered
    expect(spy).not.toHaveBeenCalled();
  });

  describe('there is a breadcrumbs container present', () => {
    it('should expand the breadcrumbs when clicked', () => {
      // Set up our document body
      document.body.innerHTML = `
      <header>
        <div data-breadcrumb-next>
          <button id="button" data-toggle-breadcrumbs>
            <svg aria-hidden="true">
              <use id="use" href="#icon-breadcrumb-expand" />
            </svg>
          </button>
          <nav aria-label="Breadcrumb">
            <span id="username" data-breadcrumb-item />
          </nav>
        </div>
      </header>`;

      expect(spy).not.toHaveBeenCalled();
      initCollapsibleBreadcrumbs();
      // event listeners registered
      expect(spy).toHaveBeenCalled();
      // click to expand the breadcrumbs
      document.getElementById('button').click();
      // click to change the button icon
      document.getElementById('button').click();
      expect(
        document.getElementById('button').getAttribute('aria-expanded'),
      ).toBe('true');
      expect(document.getElementById('use').getAttribute('href')).toBe(
        '#icon-cross',
      );
    });

    it('should collapse the breadcrumbs when clicked, if expanded', () => {
      // collapse the breadcrumbs
      document.getElementById('button').click();
      expect(
        document.getElementById('button').getAttribute('aria-expanded'),
      ).toBe('false');
      expect(document.getElementById('use').getAttribute('href')).toBe(
        '#icon-breadcrumb-expand',
      );
    });

    it('should use header based on data attribute', () => {
      document.body.innerHTML = `
      <div id="hover">
        <div data-breadcrumb-next data-header-selector="#hover">
          <button id="button" data-toggle-breadcrumbs>
            <svg aria-hidden="true">
              <use id="use" href="#icon-breadcrumb-expand" />
            </svg>
          </button>
          <nav aria-label="Breadcrumb">
            <span id="username" data-breadcrumb-item />
          </nav>
        </div>
      </div>`;

      expect(spy).not.toHaveBeenCalled();

      const containerSpy = jest.spyOn(
        document.getElementById('hover'),
        'addEventListener',
      );

      expect(containerSpy).not.toHaveBeenCalled();

      initCollapsibleBreadcrumbs();

      expect(spy).toHaveBeenLastCalledWith('keydown', expect.any(Function));
      expect(containerSpy).toHaveBeenLastCalledWith(
        'mouseenter',
        expect.any(Function),
      );
    });
  });
});
