import {
  LOCALE_NAMES,
  MAX_EXPLORER_PAGES,
  WAGTAIL_CONFIG,
} from './wagtailConfig';

describe('wagtailConfig', () => {
  describe('LOCALE_NAMES', () => {
    it('exists', () => {
      expect(LOCALE_NAMES).toBeInstanceOf(Map);
      expect(LOCALE_NAMES.get('fr')).toEqual('French');
    });
  });

  describe('MAX_EXPLORER_PAGES', () => {
    it('exists', () => {
      expect(MAX_EXPLORER_PAGES).toBeGreaterThan(0);
    });
  });

  describe('WAGTAIL_CONFIG', () => {
    it('exists', () => {
      expect(WAGTAIL_CONFIG).toEqual(
        expect.objectContaining({
          ACTIVE_CONTENT_LOCALE: expect.any(String),
          LOCALES: expect.any(Array),
        }),
      );
    });
  });
});
