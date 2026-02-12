class VersionNumberFormatError extends Error {
  constructor(versionString: string) {
    super(versionString);
    this.message = `Version number '${versionString}' is not formatted correctly.`;
  }
}

class CanOnlyComparePreReleaseVersionsError extends Error {
  constructor() {
    super();
    this.message = 'Can only compare prerelease versions';
  }
}

enum VersionDeltaType {
  MAJOR = 'Major',
  MINOR = 'Minor',
  PATCH = 'Patch',
  PRE_RELEASE_STEP = 'PreReleaseStep',
  PRE_RELEASE_VERSION = 'PreReleaseVersion',
}

class VersionNumber {
  declare major: number;
  declare minor: number;
  declare patch: number;
  declare preReleaseStep: string | null;
  declare preReleaseVersion: number | null;

  constructor(versionString: string) {
    const versionRegex =
      /^(?<major>\d+)\.{1}(?<minor>\d+)((\.{1}(?<patch>\d+))|(?<preReleaseStep>a|b|rc|\.dev){1}(?<preReleaseVersion>\d+)){0,1}$/;
    const matches = versionString.match(versionRegex);
    if (matches === null) {
      throw new VersionNumberFormatError(versionString);
    }
    const groups = matches.groups!;

    this.major = parseInt(groups.major, 10);
    this.minor = parseInt(groups.minor, 10);
    this.patch = groups.patch ? parseInt(groups.patch, 10) : 0;

    this.preReleaseStep = groups.preReleaseStep ? groups.preReleaseStep : null;
    this.preReleaseVersion = groups.preReleaseVersion
      ? parseInt(groups.preReleaseVersion, 10)
      : null;
  }

  isPreRelease() {
    return this.preReleaseStep !== null;
  }

  /**
   * Check if preReleaseStep of this versionNumber is behind another versionNumber's.
   *
   * @throws {CanOnlyComparePreReleaseVersionsError} If either version is not a pre-release.
   */
  isPreReleaseStepBehind(that: VersionNumber) {
    if (!this.isPreRelease() || !that.isPreRelease()) {
      throw new CanOnlyComparePreReleaseVersionsError();
    }

    if (
      this.preReleaseStep === 'a' &&
      (that.preReleaseStep === 'b' || that.preReleaseStep === 'rc')
    ) {
      return true;
    }
    if (this.preReleaseStep === 'b' && that.preReleaseStep === 'rc') {
      return true;
    }
    return false;
  }

  /**
   * Get VersionDeltaType that this version is behind the other version passed in.
   */
  howMuchBehind(that: VersionNumber) {
    if (this.major < that.major) {
      return VersionDeltaType.MAJOR;
    }
    if (this.major === that.major && this.minor < that.minor) {
      return VersionDeltaType.MINOR;
    }
    if (
      this.major === that.major &&
      this.minor === that.minor &&
      !this.isPreRelease() &&
      !that.isPreRelease() &&
      this.patch < that.patch
    ) {
      return VersionDeltaType.PATCH;
    }
    if (
      this.major === that.major &&
      this.minor === that.minor &&
      this.isPreRelease()
    ) {
      if (!that.isPreRelease()) {
        return VersionDeltaType.MINOR;
      }
      if (this.isPreReleaseStepBehind(that)) {
        return VersionDeltaType.PRE_RELEASE_STEP;
      }
      if (
        this.preReleaseStep === that.preReleaseStep &&
        this.preReleaseVersion! < that.preReleaseVersion!
      ) {
        return VersionDeltaType.PRE_RELEASE_VERSION;
      }
    }
    return null;
  }
}

export {
  CanOnlyComparePreReleaseVersionsError,
  VersionDeltaType,
  VersionNumber,
  VersionNumberFormatError,
};
