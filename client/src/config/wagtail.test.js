import {
  ADMIN_API,
  STRINGS,
  ADMIN_URLS,
  DATE_FORMAT,
} from './wagtail';

describe('config', () => {
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

  describe('DATE_FORMAT', () => {
    it('exists', () => {
      expect(DATE_FORMAT).toBeDefined();
    });
  });
});
