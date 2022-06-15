import { ADMIN_API, ADMIN_URLS, MAX_EXPLORER_PAGES } from './wagtailConfig';

describe('wagtailConfig', () => {
  describe('ADMIN_API', () => {
    it('exists', () => {
      expect(ADMIN_API).toBeDefined();
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
