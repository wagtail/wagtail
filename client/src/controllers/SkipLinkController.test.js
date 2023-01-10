import { initSkipLink } from './initSkipLink';

describe('initSkipLink', () => {
  document.body.innerHTML = `
  <div><a id="test" class="skiplink button" href="#main" data-skiplink="">Skip to main content</a></div>
  <main id="main">Main content</main>
  `;

  it('should add tabindex to make focusable and remove again', () => {
    const mainElement = document.getElementById('main');

    expect(document.activeElement).toBe(document.body);
    expect(mainElement.getAttribute('tabindex')).toEqual(null);

    initSkipLink();

    document.getElementById('test').click();

    expect(mainElement.getAttribute('tabindex')).toEqual('-1');
    expect(document.activeElement).toEqual(mainElement);
  });
});
