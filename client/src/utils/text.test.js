import { cleanForSlug, escapeHtml } from './text';

describe('escapeHtml', () => {
  it('should escape the supplied HTML', () => {
    expect(escapeHtml('7 is > than 5 & 3')).toEqual('7 is &gt; than 5 &amp; 3');
    expect(escapeHtml(`"push" the <button>'button'</button>`)).toEqual(
      '&quot;push&quot; the &lt;button&gt;&#039;button&#039;&lt;/button&gt;',
    );
  });
});

describe('cleanForSlug', () => {
  require('../../../wagtail/admin/static_src/wagtailadmin/js/vendor/urlify')
    .default;

  describe('cleanForSlug without unicode slugs disabled', () => {
    beforeEach(() => {
      window.unicodeSlugsEnabled = false;
    });

    it('should return a correct slug which is escaped by urlify', () => {
      /* true triggers to use django's urlify */
      expect(cleanForSlug('Before', true)).toBe('before');
      expect(cleanForSlug('The', true)).toBe('the');
      expect(cleanForSlug('Before the sun rises', true)).toBe(
        'before-the-sun-rises',
      );
      expect(cleanForSlug('ON', true)).toBe('on');
      expect(cleanForSlug('ON this day in november', true)).toBe(
        'on-this-day-in-november',
      );
      expect(cleanForSlug('This & That', true)).toBe('this-that');
      expect(cleanForSlug('The Price is $72.00!', false)).toBe(
        'the-price-is-7200',
      );
    });

    it('should return a correct slug when not escaped by urlify', () => {
      /* false triggers ignores django's urlify */
      expect(cleanForSlug('Before', false)).toBe('before');
      expect(cleanForSlug('The', false)).toBe('the');
      expect(cleanForSlug('Before the sun rises', false)).toBe(
        'before-the-sun-rises',
      );
      expect(cleanForSlug('ON', false)).toBe('on');
      expect(cleanForSlug('ON this day in november', false)).toBe(
        'on-this-day-in-november',
      );
      expect(cleanForSlug('This & That', false)).toBe('this--that');
      expect(cleanForSlug('The Price is $72.00!', false)).toBe(
        'the-price-is-7200',
      );
    });
  });

  describe('cleanForSlug without unicode slugs enabled', () => {
    beforeEach(() => {
      window.unicodeSlugsEnabled = true;
    });

    it('should return a correct slug which is escaped by urlify', () => {
      /* true triggers to use django's urlify */

      expect(cleanForSlug('This & That', true)).toBe('this-that');
      expect(cleanForSlug('The Price is $72.00!', false)).toBe(
        'the-price-is-7200',
      );
    });

    it('should return a correct slug when not escaped by urlify', () => {
      /* false triggers ignores django's urlify */

      expect(cleanForSlug('This & That', false)).toBe('this--that');
      expect(cleanForSlug('The Price is $72.00!', false)).toBe(
        'the-price-is-7200',
      );
    });
  });
});
