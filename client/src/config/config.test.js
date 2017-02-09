import {
  PAGES_ROOT_ID,
  EXPLORER_ANIM_DURATION,
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

});
