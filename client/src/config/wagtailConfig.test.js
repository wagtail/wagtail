import {
  ADMIN_API,
  STRINGS,
  ADMIN_URLS,
  MAX_EXPLORER_PAGES,
} from './wagtailConfig';

describe('wagtailConfig', () => {
  describe('ADMIN_API', () => {
    it('exists', () => {
      expect(ADMIN_API).toBeDefined();
    });
  });

  describe('STRINGS', () => {
    it('exists', () => {
      expect(STRINGS).toBeDefined();
    });
  });

  describe('ADMIN_URLS', () => {
    it('exists', () => {
      expect(ADMIN_URLS).toBeDefined();
    });
  });

  describe('MAX_EXPLORER_PAGES', () => {
    it('exists', () => {
      expect(MAX_EXPLORER_PAGES).toBeDefined();
    });
  });
});
