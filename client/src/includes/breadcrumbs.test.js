import initCollapsibleBreadcrumbs from './breadcrumbs';

describe('initCollapsibleBreadcrumbs', () => {
  it('should do nothing if there is no breadcrumbs container', () => {
    jest.spyOn(document, 'addEventListener').mockImplementation(() => {});
    // Set up our document body
    document.body.innerHTML =
      '<div>' +
      '  <span id="username" />' +
      '  <button id="button" />' +
      '</div>';
    initCollapsibleBreadcrumbs();
    // no event listeners registered
    expect(document.addEventListener).not.toHaveBeenCalled();
  });

  it('should expand the breadcrumbs when clicked', () => {
    // Set up our document body
    document.body.innerHTML =
      '<div data-slim-header>' +
      '<div data-breadcrumb-next>' +
      '  <span id="username" />' +
      '  <button id="button" data-toggle-breadcrumbs />' +
      '  <span id="username" data-breadcrumb-item hidden/>' +
      '</div>' +
      '</div>' +
      '<script>' +
      'document.getElementById("button").click();' +
      '</script>';
    document.getElementById('button').click();
    expect(document.getElementById('username').hidden).toBe(false);
  });

  it('should should collapse the breadcrumbs when clicked, if expanded', () => {});
});
