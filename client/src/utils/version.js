function versionStringToArray(versionString) {
  const trailingZeroRe = /(\.0)+[^.]*$/;
  return (versionString + '').replace(trailingZeroRe, '').split('.');
}

function compareVersion(versionA, versionB) {
  const va = versionStringToArray(versionA);
  const vb = versionStringToArray(versionB);
  const len = Math.min(va.length, vb.length);
  for (let i = 0; i < len; i++) {
    const cmp = parseInt(va[i], 10) - parseInt(vb[i], 10);
    if (cmp !== 0) {
      return cmp;
    }
  }

  return va.length - vb.length;
}

function versionOutOfDate(latestVersion, currentVersion) {
  // return true;
  return compareVersion(latestVersion, currentVersion) > 0;
}

class VersionNumberFormatError extends Error {
  constructor(versionString) {
    this.message = `Version number '${versionString}' is not formatted correctly.`;
  }
}

class VersionDeltaType {
  static MAJOR = new VersionDeltaType('Major');
  static MINOR = new VersionDeltaType('Minor');
  static PATCH = new VersionDeltaType('Patch');

  constructor(name) {
    this.name = name;
  }
}

class VersionNumber {
  constructor(versionString) {
    /* eslint-disable-next-line max-len */
    const versionRegex =
      /^(?<major>\d+)\.{1}(?<minor>\d+)((\.{1}(?<patch>\d+))|(?<preRelease>a|b|rc){1}(?<preReleaseVersion>\d+)){0,1}$/;
    const matches = versionString.match(versionRegex);
    if (matches === null) {
      throw new VersionNumberFormatError(versionString);
    }
    const groups = matches.groups;

    this.major = parseInt(groups.major, 10);
    this.minor = parseInt(groups.minor, 10);
    this.patch = groups.patch ? parseInt(groups.patch, 10) : 0;

    this.preRelease = groups.preRelease ? groups.preRelease : null;
    this.preReleaseVersion = groups.preReleaseVersion
      ? parseInt(groups.preReleaseVersion, 10)
      : null;
  }

  isPreRelease() {
    return this.preRelease !== null;
  }

  /*
   * Get VersionDeltaType that this version is behind the other version passed in.
   */
  howMuchBehind(that) {
    if (this.major < that.major) {
      return VersionDeltaType.MAJOR;
    } else if (this.minor < that.minor) {
      return VersionDeltaType.MINOR;
    } else if (
      this.minor === that.minor &&
      this.isPreRelease() &&
      !that.isPreRelease()
    ) {
      return VersionDeltaType.MINOR;
    } else {
      return null;
    }
  }
}

export {
  compareVersion,
  versionOutOfDate,
  VersionNumberFormatError,
  VersionDeltaType,
  VersionNumber,
};
