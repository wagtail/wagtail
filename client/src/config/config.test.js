import {
  PAGES_ROOT_ID,
  EXPLORER_ANIM_DURATION,
  EXPLORER_FILTERS,
} from './config';

describe('config', () => {
  describe('PAGES_ROOT_ID', () => {
    it('exists', () => {
      expect(PAGES_ROOT_ID).toBeDefined();
    });
  });

  describe('EXPLORER_ANIM_DURATION', () => {
    it('exists', () => {
      expect(EXPLORER_ANIM_DURATION).toBeDefined();
    });
  });

  describe('EXPLORER_FILTERS', () => {
    it('exists', () => {
      expect(EXPLORER_FILTERS).toBeDefined();
    });
  });
});
