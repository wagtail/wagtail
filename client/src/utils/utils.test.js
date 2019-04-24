import { versionOutOfDate } from './version';

describe('wagtail package utils', () => {
  describe('version.versionOutOfDate', () => {
    it('compares 1.5 and 2.4 correctly', () => {
      expect(versionOutOfDate('1.5', '2.4')).toBeFalsy();
    });
    it('compares 1.5.4 and 1.5.5 correctly', () => {
      expect(versionOutOfDate('1.5.4', '1.5.5')).toBeFalsy();
    });
    it('compares 1.5 and 1.5 correctly', () => {
      expect(versionOutOfDate('1.5', '1.5')).toBeFalsy();
    });
    it('compares 2.6a0 and 2.4 correctly', () => {
      expect(versionOutOfDate('2.6a0', '2.4')).toBeTruthy();
    });
  });
});
