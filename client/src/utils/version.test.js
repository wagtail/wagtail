import {
  CanOnlyComparePreReleaseVersionsError,
  VersionNumberFormatError,
  VersionNumber,
  VersionDeltaType,
} from './version';

describe('version.VersionDeltaType', () => {
  it('types equal themselves', () => {
    expect(VersionDeltaType.MAJOR).toBe(VersionDeltaType.MAJOR);
    expect(VersionDeltaType.MINOR).toBe(VersionDeltaType.MINOR);
    expect(VersionDeltaType.PATCH).toBe(VersionDeltaType.PATCH);
  });

  it('types do not equal others', () => {
    expect(VersionDeltaType.MAJOR).not.toBe(VersionDeltaType.MINOR);
    expect(VersionDeltaType.MAJOR).not.toBe(VersionDeltaType.PATCH);
    expect(VersionDeltaType.MAJOR).not.toBe(new VersionDeltaType('Other'));

    expect(VersionDeltaType.MINOR).not.toBe(VersionDeltaType.MAJOR);
    expect(VersionDeltaType.MINOR).not.toBe(VersionDeltaType.PATCH);
    expect(VersionDeltaType.MINOR).not.toBe(new VersionDeltaType('Other'));

    expect(VersionDeltaType.PATCH).not.toBe(VersionDeltaType.MAJOR);
    expect(VersionDeltaType.PATCH).not.toBe(VersionDeltaType.MINOR);
    expect(VersionDeltaType.PATCH).not.toBe(new VersionDeltaType('Other'));
  });
});

describe('version.VersionNumber initialisation', () => {
  it('initialises 1.0', () => {
    const result = new VersionNumber('1.0');

    expect(result.major).toBe(1);
    expect(result.minor).toBe(0);
    expect(result.patch).toBe(0);
  });

  it('initialises 12.0', () => {
    const result = new VersionNumber('12.0');

    expect(result.major).toBe(12);
    expect(result.minor).toBe(0);
    expect(result.patch).toBe(0);
  });

  it('initialises 2.1', () => {
    const result = new VersionNumber('2.1');

    expect(result.major).toBe(2);
    expect(result.minor).toBe(1);
    expect(result.patch).toBe(0);
  });

  it('initialises 2.13', () => {
    const result = new VersionNumber('2.13');

    expect(result.major).toBe(2);
    expect(result.minor).toBe(13);
    expect(result.patch).toBe(0);
  });

  it('initialises 2.13.0', () => {
    const result = new VersionNumber('2.13.0');

    expect(result.major).toBe(2);
    expect(result.minor).toBe(13);
    expect(result.patch).toBe(0);
  });

  it('initialises 2.13.1', () => {
    const result = new VersionNumber('2.13.1');

    expect(result.major).toBe(2);
    expect(result.minor).toBe(13);
    expect(result.patch).toBe(1);
  });

  it('initialises prerelease 2.0a0', () => {
    const result = new VersionNumber('2.0a0');

    expect(result.major).toBe(2);
    expect(result.minor).toBe(0);
    expect(result.patch).toBe(0);
    expect(result.preReleaseStep).toBe('a');
    expect(result.preReleaseVersion).toBe(0);
  });

  it('initialises prerelease 2.12a1', () => {
    const result = new VersionNumber('2.12a1');

    expect(result.major).toBe(2);
    expect(result.minor).toBe(12);
    expect(result.patch).toBe(0);
    expect(result.preReleaseStep).toBe('a');
    expect(result.preReleaseVersion).toBe(1);
  });

  it('initialises prerelease 2.12b2', () => {
    const result = new VersionNumber('2.12b2');

    expect(result.major).toBe(2);
    expect(result.minor).toBe(12);
    expect(result.patch).toBe(0);
    expect(result.preReleaseStep).toBe('b');
    expect(result.preReleaseVersion).toBe(2);
  });

  it('initialises prerelease 2.12rc23', () => {
    const result = new VersionNumber('2.12rc23');

    expect(result.major).toBe(2);
    expect(result.minor).toBe(12);
    expect(result.patch).toBe(0);
    expect(result.preReleaseStep).toBe('rc');
    expect(result.preReleaseVersion).toBe(23);
  });

  it('initialisation throws error for 1', () => {
    expect(() => new VersionNumber('1')).toThrow(VersionNumberFormatError);
  });

  it('initialisation throws error for 1a', () => {
    expect(() => new VersionNumber('1a')).toThrow(VersionNumberFormatError);
  });

  it('initialisation throws error for 1a0', () => {
    expect(() => new VersionNumber('1a0')).toThrow(VersionNumberFormatError);
  });

  it('initialisation throws error for 1.0.0a0', () => {
    expect(() => new VersionNumber('1.0.0a0')).toThrow(
      VersionNumberFormatError,
    );
  });

  it('initialisation throws error for text string', () => {
    expect(() => new VersionNumber('not a number')).toThrow(
      VersionNumberFormatError,
    );
  });
});

describe('version.VersionNumber.isPreRelease', () => {
  it('responds correctly for 1.0a0', () => {
    const versionNumber = new VersionNumber('1.0a0');
    expect(versionNumber.isPreRelease()).toBe(true);
  });

  it('responds correctly for 1.1a1', () => {
    const versionNumber = new VersionNumber('1.1a1');
    expect(versionNumber.isPreRelease()).toBe(true);
  });

  it('responds correctly for 1.1', () => {
    const versionNumber = new VersionNumber('1.1');
    expect(versionNumber.isPreRelease()).toBe(false);
  });

  it('responds correctly for 1.1.1', () => {
    const versionNumber = new VersionNumber('1.1.1');
    expect(versionNumber.isPreRelease()).toBe(false);
  });
});

describe('version.VersionNumber.isPreReleaseStepBehind', () => {
  it('responds correctly for 1.0a0 v 1.0a0', () => {
    const thisVersion = new VersionNumber('1.0a0');
    const thatVersion = new VersionNumber('1.0a0');
    expect(thisVersion.isPreReleaseStepBehind(thatVersion)).toBe(false);
  });
  it('responds correctly for 1.0a0 v 1.0b0', () => {
    const thisVersion = new VersionNumber('1.0a0');
    const thatVersion = new VersionNumber('1.0b0');
    expect(thisVersion.isPreReleaseStepBehind(thatVersion)).toBe(true);
  });
  it('responds correctly for 1.0a0 v 1.0rc0', () => {
    const thisVersion = new VersionNumber('1.0a0');
    const thatVersion = new VersionNumber('1.0rc0');
    expect(thisVersion.isPreReleaseStepBehind(thatVersion)).toBe(true);
  });
  it('responds correctly for 1.0b0 v 1.0a0', () => {
    const thisVersion = new VersionNumber('1.0b0');
    const thatVersion = new VersionNumber('1.0a0');
    expect(thisVersion.isPreReleaseStepBehind(thatVersion)).toBe(false);
  });
  it('responds correctly for 1.0b0 v 1.0b0', () => {
    const thisVersion = new VersionNumber('1.0b0');
    const thatVersion = new VersionNumber('1.0b0');
    expect(thisVersion.isPreReleaseStepBehind(thatVersion)).toBe(false);
  });
  it('responds correctly for 1.0b0 v 1.0rc0', () => {
    const thisVersion = new VersionNumber('1.0b0');
    const thatVersion = new VersionNumber('1.0rc0');
    expect(thisVersion.isPreReleaseStepBehind(thatVersion)).toBe(true);
  });
  it('responds correctly for 1.0rc0 v 1.0a0', () => {
    const thisVersion = new VersionNumber('1.0rc0');
    const thatVersion = new VersionNumber('1.0a0');
    expect(thisVersion.isPreReleaseStepBehind(thatVersion)).toBe(false);
  });
  it('responds correctly for 1.0rc0 v 1.0b0', () => {
    const thisVersion = new VersionNumber('1.0rc0');
    const thatVersion = new VersionNumber('1.0b0');
    expect(thisVersion.isPreReleaseStepBehind(thatVersion)).toBe(false);
  });
  it('responds correctly for 1.0rc0 v 1.0rc0', () => {
    const thisVersion = new VersionNumber('1.0rc0');
    const thatVersion = new VersionNumber('1.0rc0');
    expect(thisVersion.isPreReleaseStepBehind(thatVersion)).toBe(false);
  });

  it('throws error for this being non-prerelease version', () => {
    const thisVersion = new VersionNumber('1.0.0');
    const thatVersion = new VersionNumber('1.0rc0');
    expect(() => thisVersion.isPreReleaseStepBehind(thatVersion)).toThrowError(
      CanOnlyComparePreReleaseVersionsError,
    );
  });
  it('throws error for that being non-prerelease version', () => {
    const thisVersion = new VersionNumber('1.0rc0');
    const thatVersion = new VersionNumber('1.0.0');
    expect(() => thisVersion.isPreReleaseStepBehind(thatVersion)).toThrowError(
      CanOnlyComparePreReleaseVersionsError,
    );
  });
});

describe('version.VersionNumber.howMuchBehind', () => {
  // MAJOR
  it('correctly compares 1.0 to 2.0', () => {
    const thisVersion = new VersionNumber('1.0');
    const thatVersion = new VersionNumber('2.0');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(VersionDeltaType.MAJOR);
  });
  it('correctly compares 1.2 to 2.1', () => {
    const thisVersion = new VersionNumber('1.2');
    const thatVersion = new VersionNumber('2.1');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(VersionDeltaType.MAJOR);
  });
  it('correctly compares 1.0rc0 to 2.0', () => {
    const thisVersion = new VersionNumber('1.0rc0');
    const thatVersion = new VersionNumber('2.0');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(VersionDeltaType.MAJOR);
  });

  // MINOR
  it('correctly compares 1.0 to 1.1', () => {
    const thisVersion = new VersionNumber('1.0');
    const thatVersion = new VersionNumber('1.1');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(VersionDeltaType.MINOR);
  });
  it('correctly compares 1.1.0 to 1.2.0', () => {
    const thisVersion = new VersionNumber('1.1.0');
    const thatVersion = new VersionNumber('1.2.0');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(VersionDeltaType.MINOR);
  });
  it('correctly compares 1.0a0 to 1.0', () => {
    const thisVersion = new VersionNumber('1.0a0');
    const thatVersion = new VersionNumber('1.0');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(VersionDeltaType.MINOR);
  });
  it('correctly compares 1.0a1 to 1.0', () => {
    const thisVersion = new VersionNumber('1.0a1');
    const thatVersion = new VersionNumber('1.0');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(VersionDeltaType.MINOR);
  });
  it('correctly compares 1.0a1 to 1.0.1', () => {
    const thisVersion = new VersionNumber('1.0a1');
    const thatVersion = new VersionNumber('1.0.1');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(VersionDeltaType.MINOR);
  });
  it('correctly compares 1.0a0 to 1.1', () => {
    const thisVersion = new VersionNumber('1.0a0');
    const thatVersion = new VersionNumber('1.1');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(VersionDeltaType.MINOR);
  });
  it('correctly compares 1.0a0 to 1.1a0', () => {
    const thisVersion = new VersionNumber('1.0a0');
    const thatVersion = new VersionNumber('1.1a0');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(VersionDeltaType.MINOR);
  });

  // PATCH
  it('correctly compares 1.0.0 to 1.0.1', () => {
    const thisVersion = new VersionNumber('1.0.0');
    const thatVersion = new VersionNumber('1.0.1');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(VersionDeltaType.PATCH);
  });
  it('correctly compares 1.0.0 to 1.0.2', () => {
    const thisVersion = new VersionNumber('1.0.0');
    const thatVersion = new VersionNumber('1.0.2');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(VersionDeltaType.PATCH);
  });

  // PRE_RELEASE_STEP
  it('correctly compares 1.0a0 to 1.0b0', () => {
    const thisVersion = new VersionNumber('1.0a0');
    const thatVersion = new VersionNumber('1.0b0');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(VersionDeltaType.PRE_RELEASE_STEP);
  });
  it('correctly compares 1.0a0 to 1.0rc0', () => {
    const thisVersion = new VersionNumber('1.0a0');
    const thatVersion = new VersionNumber('1.0rc0');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(VersionDeltaType.PRE_RELEASE_STEP);
  });
  it('correctly compares 1.0b0 to 1.0rc0', () => {
    const thisVersion = new VersionNumber('1.0b0');
    const thatVersion = new VersionNumber('1.0rc0');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(VersionDeltaType.PRE_RELEASE_STEP);
  });

  // PRE_RELEASE_VERSION
  it('correctly compares 1.0a0 to 1.0a1', () => {
    const thisVersion = new VersionNumber('1.0a0');
    const thatVersion = new VersionNumber('1.0a1');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(VersionDeltaType.PRE_RELEASE_VERSION);
  });
  it('correctly compares 1.0b0 to 1.0b1', () => {
    const thisVersion = new VersionNumber('1.0b0');
    const thatVersion = new VersionNumber('1.0b1');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(VersionDeltaType.PRE_RELEASE_VERSION);
  });
  it('correctly compares 1.0rc0 to 1.0rc1', () => {
    const thisVersion = new VersionNumber('1.0rc0');
    const thatVersion = new VersionNumber('1.0rc1');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(VersionDeltaType.PRE_RELEASE_VERSION);
  });

  // null
  it('correctly compares 1.0 to 1.0', () => {
    const thisVersion = new VersionNumber('1.0');
    const thatVersion = new VersionNumber('1.0');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(null);
  });
  it('correctly compares 2.0 to 1.0', () => {
    const thisVersion = new VersionNumber('2.0');
    const thatVersion = new VersionNumber('1.0');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(null);
  });
  it('correctly compares 1.1 to 1.1', () => {
    const thisVersion = new VersionNumber('1.1');
    const thatVersion = new VersionNumber('1.1');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(null);
  });
  it('correctly compares 1.2 to 1.1', () => {
    const thisVersion = new VersionNumber('1.2');
    const thatVersion = new VersionNumber('1.1');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(null);
  });
  it('correctly compares 2.0 to 1.1', () => {
    const thisVersion = new VersionNumber('2.0');
    const thatVersion = new VersionNumber('1.1');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(null);
  });
  it('correctly compares 1.1.1 to 1.1.1', () => {
    const thisVersion = new VersionNumber('1.1.1');
    const thatVersion = new VersionNumber('1.1.1');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(null);
  });
  it('correctly compares 1.1.2 to 1.1.1', () => {
    const thisVersion = new VersionNumber('1.1.2');
    const thatVersion = new VersionNumber('1.1.1');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(null);
  });
  it('correctly compares 1.2.1 to 1.1.2', () => {
    const thisVersion = new VersionNumber('1.2.1');
    const thatVersion = new VersionNumber('1.1.2');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(null);
  });
  it('correctly compares 1.1a1 to 1.1a1', () => {
    const thisVersion = new VersionNumber('1.1a1');
    const thatVersion = new VersionNumber('1.1a1');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(null);
  });
  it('correctly compares 1.1b1 to 1.1a1', () => {
    const thisVersion = new VersionNumber('1.1b1');
    const thatVersion = new VersionNumber('1.1a1');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(null);
  });
  it('correctly compares 2.0a0 to 1.0', () => {
    const thisVersion = new VersionNumber('2.0a0');
    const thatVersion = new VersionNumber('1.0');

    const result = thisVersion.howMuchBehind(thatVersion);

    expect(result).toBe(null);
  });
});
