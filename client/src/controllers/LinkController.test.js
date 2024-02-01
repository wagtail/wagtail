import { Application } from '@hotwired/stimulus';
import { LinkController } from './LinkController';

describe('LinkController', () => {
  let app;
  const oldWindowLocation = window.location;

  const setWindowLocation = (url) => {
    delete window.location;
    window.location = new URL(url);
  };

  beforeEach(() => {
    app = Application.start();
    app.register('w-link', LinkController);
  });

  afterEach(() => {
    app?.stop();
    jest.clearAllMocks();
    window.location = oldWindowLocation;
  });

  describe('basic behaviour on connect', () => {
    it('should reflect all params by default', async () => {
      setWindowLocation(
        'http://localhost:8000/admin/pages/?foo=bar&foo=baz&hello=&world=ok',
      );
      expect(window.location.href).toEqual(
        'http://localhost:8000/admin/pages/?foo=bar&foo=baz&hello=&world=ok',
      );

      document.body.innerHTML = `
        <a
          id="link"
          href="/admin/something/"
          data-controller="w-link"
        >
          Reflective link
        </a>
      `;

      // Trigger next browser render cycle
      await Promise.resolve();

      // All params are reflected as-is, including multi-value and empty params
      // and the relative URL is resolved against the current URL
      expect(document.getElementById('link').href).toEqual(
        'http://localhost:8000/admin/something/?foo=bar&foo=baz&hello=&world=ok',
      );
      // The current URL is not changed
      expect(window.location.href).toEqual(
        'http://localhost:8000/admin/pages/?foo=bar&foo=baz&hello=&world=ok',
      );
    });

    it('should only apply params in reflect-keys-value', async () => {
      setWindowLocation(
        'http://localhost:8000/admin/pages/?foo=bar&foo=baz&hello=&world=ok',
      );
      expect(window.location.href).toEqual(
        'http://localhost:8000/admin/pages/?foo=bar&foo=baz&hello=&world=ok',
      );

      document.body.innerHTML = `
        <a
          id="link"
          href="/admin/something/"
          data-controller="w-link"
          data-w-link-reflect-keys-value='["foo", "hello"]'
        >
          Selectively reflective link
        </a>
      `;

      // Trigger next browser render cycle
      await Promise.resolve();

      // Only the specified params are reflected
      expect(document.getElementById('link').href).toEqual(
        'http://localhost:8000/admin/something/?foo=bar&foo=baz&hello=',
      );
      // The current URL is not changed
      expect(window.location.href).toEqual(
        'http://localhost:8000/admin/pages/?foo=bar&foo=baz&hello=&world=ok',
      );
    });

    it('should preserve params in preserve-keys-value', async () => {
      setWindowLocation(
        'http://localhost:8000/admin/pages/?foo=bar&foo=baz&hello=&world=ok&a=z',
      );
      expect(window.location.href).toEqual(
        'http://localhost:8000/admin/pages/?foo=bar&foo=baz&hello=&world=ok&a=z',
      );

      document.body.innerHTML = `
        <a
          id="link"
          href="/admin/something/?export=xlsx&export=csv&foo=fii&number=1&a=b"
          data-controller="w-link"
          data-w-link-preserve-keys-value='["export", "foo"]'
        >
          Reflective link with preserve-keys-value
        </a>
      `;

      // Trigger next browser render cycle
      await Promise.resolve();

      // Behaviour:
      // - `export` param preserved (multi-value, not in new URL)
      // - `foo` param preserved (single value, available in new URL)
      // - `number` param not preserved (single value, not in new URL)
      // - `hello` param reflected (empty value, only available in new URL)
      // - `world` param reflected (single value, only available in new URL)
      // - `a` param reflected (single value, available in both, taken from new URL)
      expect(document.getElementById('link').href).toEqual(
        'http://localhost:8000/admin/something/?hello=&world=ok&a=z&export=xlsx&export=csv&foo=fii',
      );
      // The current URL is not changed
      expect(window.location.href).toEqual(
        'http://localhost:8000/admin/pages/?foo=bar&foo=baz&hello=&world=ok&a=z',
      );
    });

    it('should reflect only the keys in reflect-keys-value and keep keys in preserve-keys-value', async () => {
      setWindowLocation(
        'http://localhost:8000/admin/pages/?foo=bar&foo=baz&hello=&world=ok&a=z',
      );
      expect(window.location.href).toEqual(
        'http://localhost:8000/admin/pages/?foo=bar&foo=baz&hello=&world=ok&a=z',
      );

      document.body.innerHTML = `
        <a
          id="link"
          href="/admin/something/?export=xlsx&export=csv&foo=fii&number=1&a=b"
          data-controller="w-link"
          data-w-link-reflect-keys-value='["hello", "a"]'
          data-w-link-preserve-keys-value='["export", "foo"]'
        >
          Reflective link with reflect-keys-value and preserve-keys-value
        </a>
      `;

      // Trigger next browser render cycle
      await Promise.resolve();

      // Behaviour:
      // - `export` param preserved (multi-value, not in new URL)
      // - `foo` param preserved (single value, available in new URL)
      // - `number` param not preserved (single value, not in new URL)
      // - `hello` param reflected (empty value, only available in new URL)
      // - `world` param not reflected (single value, only available in new URL)
      // - `a` param reflected (single value, available in both, taken from new URL)
      expect(document.getElementById('link').href).toEqual(
        'http://localhost:8000/admin/something/?hello=&a=z&export=xlsx&export=csv&foo=fii',
      );
      // The current URL is not changed
      expect(window.location.href).toEqual(
        'http://localhost:8000/admin/pages/?foo=bar&foo=baz&hello=&world=ok&a=z',
      );
    });
  });

  describe('handling an event with requestUrl in the detail', () => {
    it('should reflect all params by default', async () => {
      expect(window.location.href).toEqual('http://localhost/');

      document.body.innerHTML = `
        <a
          id="link"
          href="/admin/something/"
          data-controller="w-link"
          data-action="w-swap:reflect@document->w-link#setParams"
        >
          Reflective link
        </a>
      `;

      // Trigger next browser render cycle
      await Promise.resolve();

      document.dispatchEvent(
        new CustomEvent('w-swap:reflect', {
          detail: {
            requestUrl:
              'http://localhost:8000/admin/pages/?foo=bar&foo=baz&hello=&world=ok',
          },
        }),
      );

      // All params are reflected as-is, including multi-value and empty params
      // and the relative URL is resolved against the current URL
      expect(document.getElementById('link').href).toEqual(
        'http://localhost/admin/something/?foo=bar&foo=baz&hello=&world=ok',
      );
    });

    it('should only apply params in reflect-keys-value', async () => {
      expect(window.location.href).toEqual('http://localhost/');

      document.body.innerHTML = `
        <a
          id="link"
          href="/admin/something/"
          data-controller="w-link"
          data-w-link-reflect-keys-value='["foo", "hello"]'
          data-action="w-swap:reflect@document->w-link#setParams"
        >
          Selectively reflective link
        </a>
      `;

      // Trigger next browser render cycle
      await Promise.resolve();

      document.dispatchEvent(
        new CustomEvent('w-swap:reflect', {
          detail: {
            requestUrl:
              'http://localhost:8000/admin/pages/?foo=bar&foo=baz&hello=&world=ok',
          },
        }),
      );

      // Only the specified params are reflected
      expect(document.getElementById('link').href).toEqual(
        'http://localhost/admin/something/?foo=bar&foo=baz&hello=',
      );
    });

    it('should preserve params in preserve-keys-value', async () => {
      expect(window.location.href).toEqual('http://localhost/');

      document.body.innerHTML = `
        <a
          id="link"
          href="/admin/something/?export=xlsx&export=csv&foo=fii&number=1&a=b"
          data-controller="w-link"
          data-w-link-preserve-keys-value='["export", "foo"]'
          data-action="w-swap:reflect@document->w-link#setParams"
        >
          Reflective link with preserve-keys-value
        </a>
      `;

      // Trigger next browser render cycle
      await Promise.resolve();

      document.dispatchEvent(
        new CustomEvent('w-swap:reflect', {
          detail: {
            requestUrl:
              'http://localhost:8000/admin/pages/?foo=bar&foo=baz&hello=&world=ok&a=z',
          },
        }),
      );

      // Behaviour:
      // - `export` param preserved (multi-value, not in new URL)
      // - `foo` param preserved (single value, available in new URL)
      // - `number` param not preserved (single value, not in new URL)
      // - `hello` param reflected (empty value, only available in new URL)
      // - `world` param reflected (single value, only available in new URL)
      // - `a` param reflected (single value, available in both, taken from new URL)
      expect(document.getElementById('link').href).toEqual(
        'http://localhost/admin/something/?hello=&world=ok&a=z&export=xlsx&export=csv&foo=fii',
      );
    });

    it('should reflect only the keys in reflect-keys-value and keep keys in preserve-keys-value', async () => {
      expect(window.location.href).toEqual('http://localhost/');

      document.body.innerHTML = `
        <a
          id="link"
          href="/admin/something/?export=xlsx&export=csv&foo=fii&number=1&a=b"
          data-controller="w-link"
          data-w-link-reflect-keys-value='["hello", "a"]'
          data-w-link-preserve-keys-value='["export", "foo"]'
          data-action="w-swap:reflect@document->w-link#setParams"
        >
          Reflective link with reflect-keys-value and preserve-keys-value
        </a>
      `;

      // Trigger next browser render cycle
      await Promise.resolve();

      document.dispatchEvent(
        new CustomEvent('w-swap:reflect', {
          detail: {
            requestUrl:
              'http://localhost:8000/admin/pages/?foo=bar&foo=baz&hello=&world=ok&a=z',
          },
        }),
      );

      // Behaviour:
      // - `export` param preserved (multi-value, not in new URL)
      // - `foo` param preserved (single value, available in new URL)
      // - `number` param not preserved (single value, not in new URL)
      // - `hello` param reflected (empty value, only available in new URL)
      // - `world` param not reflected (single value, only available in new URL)
      // - `a` param reflected (single value, available in both, taken from new URL)
      expect(document.getElementById('link').href).toEqual(
        'http://localhost/admin/something/?hello=&a=z&export=xlsx&export=csv&foo=fii',
      );
    });
  });

  describe('handling an event without requestUrl in the detail', () => {
    it('should not reflect any params', async () => {
      expect(window.location.href).toEqual('http://localhost/');

      document.body.innerHTML = `
        <a
          id="link"
          href="/admin/something/"
          data-controller="w-link"
          data-action="custom:event@document->w-link#setParams"
        >
          Reflective link
        </a>
      `;

      // Trigger next browser render cycle
      await Promise.resolve();

      document.dispatchEvent(
        new CustomEvent('custom:event', {
          detail: {
            something: 'else',
          },
        }),
      );

      // Should not change the href
      expect(document.getElementById('link').href).toEqual(
        'http://localhost/admin/something/',
      );
    });
  });

  describe('using a custom attr-name-value for the link', () => {
    it('should reflect the params from the current URL to the link in the specified attribute', async () => {
      setWindowLocation(
        'http://localhost:8000/admin/pages/?foo=bar&foo=baz&hello=&world=ok&a=z',
      );
      expect(window.location.href).toEqual(
        'http://localhost:8000/admin/pages/?foo=bar&foo=baz&hello=&world=ok&a=z',
      );

      document.body.innerHTML = `
        <button
          id="button"
          data-target-url="/admin/something/?export=xlsx&export=csv&foo=fii&number=1&a=b"
          data-controller="w-link"
          data-w-link-attr-name-value="data-target-url"
          data-w-link-reflect-keys-value='["hello", "a"]'
          data-w-link-preserve-keys-value='["export", "foo"]'
        >
          Reflective link with attr-name-value, reflect-keys-value, and preserve-keys-value
        </button>
      `;

      // Trigger next browser render cycle
      await Promise.resolve();

      // Behaviour:
      // - `export` param preserved (multi-value, not in new URL)
      // - `foo` param preserved (single value, available in new URL)
      // - `number` param not preserved (single value, not in new URL)
      // - `hello` param reflected (empty value, only available in new URL)
      // - `world` param not reflected (single value, only available in new URL)
      // - `a` param reflected (single value, available in both, taken from new URL)
      expect(document.getElementById('button').dataset.targetUrl).toEqual(
        'http://localhost:8000/admin/something/?hello=&a=z&export=xlsx&export=csv&foo=fii',
      );
      // The current URL is not changed
      expect(window.location.href).toEqual(
        'http://localhost:8000/admin/pages/?foo=bar&foo=baz&hello=&world=ok&a=z',
      );
    });

    it("should reflect the params from the event's requestUrl to the link in the specified attribute", async () => {
      expect(window.location.href).toEqual('http://localhost/');

      document.body.innerHTML = `
        <button
          id="button"
          data-target-url="/admin/something/?export=xlsx&export=csv&foo=fii&number=1&a=b"
          data-controller="w-link"
          data-w-link-attr-name-value="data-target-url"
          data-w-link-reflect-keys-value='["hello", "a"]'
          data-w-link-preserve-keys-value='["export", "foo"]'
          data-action="w-swap:reflect@document->w-link#setParams"
        >
          Reflective link with attr-name-value, reflect-keys-value, and preserve-keys-value
        </button>
      `;

      // Trigger next browser render cycle
      await Promise.resolve();

      document.dispatchEvent(
        new CustomEvent('w-swap:reflect', {
          detail: {
            requestUrl:
              'http://localhost:8000/admin/pages/?foo=bar&foo=baz&hello=&world=ok&a=z',
          },
        }),
      );

      // Behaviour:
      // - `export` param preserved (multi-value, not in new URL)
      // - `foo` param preserved (single value, available in new URL)
      // - `number` param not preserved (single value, not in new URL)
      // - `hello` param reflected (empty value, only available in new URL)
      // - `world` param not reflected (single value, only available in new URL)
      // - `a` param reflected (single value, available in both, taken from new URL)
      expect(document.getElementById('button').dataset.targetUrl).toEqual(
        'http://localhost/admin/something/?hello=&a=z&export=xlsx&export=csv&foo=fii',
      );
    });
  });
});
