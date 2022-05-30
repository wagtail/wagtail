import initCollapsibleBreadcrumbs from './breadcrumbs';

describe('initCollapsibleBreadcrumbs', () => {
  const spy = jest.spyOn(document, 'addEventListener');
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
<div data-slim-header>
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
</div>`;
      initCollapsibleBreadcrumbs();
      // event listeners registered
      expect(spy).toHaveBeenCalled();
      // click to expand the breadcumbs
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
  });
});
