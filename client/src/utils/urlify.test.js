import { urlify } from './urlify';

describe('urlify', () => {
  describe('urlify with unicode slugs disabled (default)', () => {
    it('should return a correct slug which is escaped by urlify', () => {
      expect(urlify('This & That')).toBe('this-that');
      expect(urlify('The Price is $72.00!')).toBe('the-price-is-7200');
      expect(urlify('Lisboa é ótima à beira-mar')).toBe(
        'lisboa-e-otima-a-beira-mar',
      );
    });
  });

  describe('urlify with unicode slugs enabled', () => {
    const options = { allowUnicode: true };

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
      expect(urlify('The Price is $72.00!', options)).toBe('the-price-is-7200');
      expect(urlify('Lisboa é ótima à beira-mar', options)).toBe(
        'lisboa-é-ótima-à-beira-mar',
      );
    });
  });
});
