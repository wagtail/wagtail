import { runInlineScripts } from './runInlineScripts';

describe('runInlineScripts', () => {
  it('runs inline scripts when invoked on container', () => {
    window.foo = 'foo';

    const div = document.createElement('div');
    document.body.appendChild(div);
    div.innerHTML = '<script data-foo="foo">window.foo = "bar";</script>';

    expect(window.foo).toBe('foo');
    runInlineScripts(div);
    expect(window.foo).toBe('bar');
  });

  it('ignores non-javascript scripts', () => {
    window.foo = 'foo';

    const div = document.createElement('div');
    document.body.appendChild(div);
    div.innerHTML =
      '<script type="application/x-piratescript">window.foo = "yarrr";</script>';

    runInlineScripts(div);
    expect(window.foo).toBe('foo');
  });

  it('runs inline scripts when invoked on script element', () => {
    window.foo = 'foo';

    const div = document.createElement('div');
    document.body.appendChild(div);
    div.innerHTML = '<script data-foo>window.foo = "bar";</script>';

    expect(window.foo).toBe('foo');
    runInlineScripts(div.querySelector('script'));
    expect(window.foo).toBe('bar');
  });
});
