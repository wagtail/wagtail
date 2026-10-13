import { isWithinPath } from './MenuItem';

describe('isWithinPath', () => {
  it('should match the same path', () => {
    expect(isWithinPath('.reports', '.reports')).toBe(true);
  });

  it('should match a nested path', () => {
    expect(isWithinPath('.reports.workflows', '.reports')).toBe(true);
    expect(isWithinPath('.settings.users.groups', '.settings')).toBe(true);
  });

  it('should not match a sibling path that shares a prefix', () => {
    // See https://github.com/wagtail/wagtail/issues/10313
    expect(isWithinPath('.qualtrics-360', '.qualtrics')).toBe(false);
    expect(isWithinPath('.qualtrics360.surveys', '.qualtrics')).toBe(false);
  });

  it('should not match a parent path', () => {
    expect(isWithinPath('.reports', '.reports.workflows')).toBe(false);
  });

  it('should not match an empty path', () => {
    expect(isWithinPath('', '.reports')).toBe(false);
  });
});
