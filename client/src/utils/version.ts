const VERSION_DELTA_TYPE = {
  MAJOR: 'VERSION_DELTA_TYPE_MAJOR',
  MINOR: 'VERSION_DELTA_TYPE_MINOR',
  PATCH: 'VERSION_DELTA_TYPE_PATCH',
  PRE_RELEASE_STEP: 'VERSION_DELTA_TYPE_PRE_RELEASE_STEP',
  PRE_RELEASE_VERSION: 'VERSION_DELTA_TYPE_PRE_RELEASE_VERSION',
};

class VersionNumber {
  major: number;

  minor: number;

  patch: number;

  preReleaseStep: any;

  preReleaseVersion: number;

  constructor(versionString) {
    const versionRegex =
      /^(?<major>\d+)\.{1}(?<minor>\d+)((\.{1}(?<patch>\d+))|(?<preReleaseStep>a|b|rc){1}(?<preReleaseVersion>\d+)){0,1}$/;
    const matches = versionString.match(versionRegex);
    if (matches === null) {
      throw new Error(
        `Version number '${versionString}' is not formatted correctly.`,
      );
    }
    const { groups } = matches;

    this.major = parseInt(groups.major, 10);
    this.minor = parseInt(groups.minor, 10);
    this.patch = groups.patch ? parseInt(groups.patch, 10) : 0;

    this.preReleaseStep = groups.preReleaseStep ? groups.preReleaseStep : null;
    this.preReleaseVersion = groups.preReleaseVersion
      ? parseInt(groups.preReleaseVersion, 10)
      : 0;
  }

  isPreRelease() {
    return this.preReleaseStep !== null;
  }

  /*
   * Check if preReleaseStep of this versionNumber is behind another versionNumber's.
   */
  isPreReleaseStepBehind(that) {
    if (!this.isPreRelease() || !that.isPreRelease()) {
      throw new Error('Can only compare prerelease versions');
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

  /*
   * Get version delta type that this version is behind the other version passed in.
   */
  howMuchBehind(that) {
    if (this.major < that.major) {
      return VERSION_DELTA_TYPE.MAJOR;
    }
    if (this.major === that.major && this.minor < that.minor) {
      return VERSION_DELTA_TYPE.MINOR;
    }
    if (
      this.major === that.major &&
      this.minor === that.minor &&
      !this.isPreRelease() &&
      !that.isPreRelease() &&
      this.patch < that.patch
    ) {
      return VERSION_DELTA_TYPE.PATCH;
    }
    if (
      this.major === that.major &&
      this.minor === that.minor &&
      this.isPreRelease()
    ) {
      if (!that.isPreRelease()) {
        return VERSION_DELTA_TYPE.MINOR;
      }
      if (this.isPreReleaseStepBehind(that)) {
        return VERSION_DELTA_TYPE.PRE_RELEASE_STEP;
      }
      if (
        this.preReleaseStep === that.preReleaseStep &&
        this.preReleaseVersion < that.preReleaseVersion
      ) {
        return VERSION_DELTA_TYPE.PRE_RELEASE_VERSION;
      }
    }
    return null;
  }
}

export { VERSION_DELTA_TYPE, VersionNumber };
