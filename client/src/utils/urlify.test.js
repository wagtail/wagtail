import { urlify } from './urlify';

describe('urlify', () => {
  beforeAll(() => {
    // load window.URLify
    require('../../../wagtail/admin/static_src/wagtailadmin/js/vendor/urlify')
      .default;
  });

  describe('urlify with unicode slugs disabled (default)', () => {
    it('should return a correct slug which is escaped by urlify', () => {
      expect(urlify('This & That')).toBe('this-that');

      expect(urlify('Lisboa é ótima à beira-mar')).toBe(
        'lisboa-e-otima-a-beira-mar',
      );
    });
  });

  describe('urlify with unicode slugs enabled', () => {
    const options = { unicodeSlugsEnabled: true };

    it('should return a correct slug which is escaped by urlify', () => {
      expect(urlify('Before', options)).toBe('before');
      expect(urlify('The', options)).toBe('the');
      expect(urlify('Before the sun rises', options)).toBe(
        'before-the-sun-rises',
      );
      expect(urlify('ON', options)).toBe('on');
      expect(urlify('ON this day in november', options)).toBe(
        'on-this-day-in-november',
      );
      expect(urlify('This & That', options)).toBe('this-that');

      expect(urlify('Lisboa é ótima à beira-mar', options)).toBe(
        'lisboa-e-otima-a-beira-mar',
      );
    });
  });
});
