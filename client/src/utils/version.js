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
  //return true;
  return compareVersion(latestVersion, currentVersion) > 0;
}

class VersionNumberFormatError extends Error {
  constructor(versionString) {
    this.message = `Version number '${versionString}' is not formatted correctly.`;
  }
}

class VersionNumber {
  constructor(versionString) {
    const versionRegex =
      /^(?<major>\d+)\.{1}(?<minor>\d+)((\.{1}(?<patch>\d+))|(?<preRelease>a|b|rc){1}(?<preReleaseVersion>\d+)){0,1}$/;
    const matches = versionString.match(versionRegex);
    if (matches === null) {
      throw new VersionNumberFormatError(versionString);
    }
    const groups = matches.groups;

    this.major = parseInt(groups.major);
    this.minor = parseInt(groups.minor);
    this.patch = groups.patch ? parseInt(groups.patch) : 0;

    this.preRelease = groups.preRelease ? groups.preRelease : null;
    this.preReleaseVersion = groups.preReleaseVersion
      ? parseInt(groups.preReleaseVersion)
      : null;
  }
}

export {
  compareVersion,
  versionOutOfDate,
  VersionNumberFormatError,
  VersionNumber,
};
