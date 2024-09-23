import { slugify } from './slugify';

describe('slugify', () => {
  describe('slugify with unicode slugs disabled (default)', () => {
    it('should return a correct slug', () => {
      expect(slugify('The Price is $72.00!')).toBe('the-price-is-7200');
      expect(slugify('This & That')).toBe('this--that');
      expect(slugify('Lisboa é ótima à beira-mar')).toBe(
        'lisboa--tima--beira-mar',
      );
    });
  });

  describe('slugify with unicode slugs enabled', () => {
    const options = { allowUnicode: true };

    it('should return a correct slug', () => {
      expect(slugify('The Price is $72.00!', options)).toBe(
        'the-price-is-7200',
      );
      expect(slugify('Before', options)).toBe('before');
      expect(slugify('The', options)).toBe('the');
      expect(slugify('Before the sun rises', options)).toBe(
        'before-the-sun-rises',
      );
      expect(slugify('ON', options)).toBe('on');
      expect(slugify('ON this day in november', options)).toBe(
        'on-this-day-in-november',
      );
      expect(slugify('This & That', options)).toBe('this--that');
      expect(slugify('Lisboa é ótima à beira-mar', options)).toBe(
        'lisboa-é-ótima-à-beira-mar',
      );
      expect(slugify('উইকিপিডিয়ায় স্বাগতম!', options)).toBe('উইকপডযয-সবগতম');
    });
  });
});
