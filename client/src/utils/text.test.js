import { escapeHtml } from './text';

describe('escapeHtml', () => {
  it('should escape the supplied HTML', () => {
    expect(escapeHtml('7 is > than 5 & 3')).toEqual('7 is &gt; than 5 &amp; 3');
    expect(escapeHtml(`"push" the <button>'button'</button>`)).toEqual(
      '&quot;push&quot; the &lt;button&gt;&#039;button&#039;&lt;/button&gt;',
    );
  });
});
