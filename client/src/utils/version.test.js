import { compareVersion, versionOutOfDate, VersionNumber } from './version';

describe('version.compareVersion', () => {
  it('compares 1.12 and 1.11 correctly', () => {
    expect(compareVersion('1.12', '1.11')).toBe(1);
  });

  it('compares 2 and 1 correctly', () => {
    expect(compareVersion('2', '1')).toBe(1);
  });

  it('compares 1 and 3 correctly', () => {
    expect(compareVersion('1', '3')).toBe(-2);
  });

  it('compares 2.1 and 2 correctly', () => {
    expect(compareVersion('2.1', '2')).toBe(1);
  });

  it('compares 2.1.1 and 2 correctly', () => {
    expect(compareVersion('2.1.1', '2')).toBe(2);
  });
});

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
  it.skip('compares 2.6a0 and 2.6 correctly', () => {
    expect(versionOutOfDate('2.6a0', '2.6')).toBeTruthy();
  });
});

describe('version.VersionNumber', () => {
  it('initialises 1', () => {
    const result = new VersionNumber('1');

    expect(result.full).toBe(1);
    expect(result.major).toBe(0);
    expect(result.patch).toBe(0);
  });
});
