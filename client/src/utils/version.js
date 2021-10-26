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

class VersionNumber {
  constructor(versionString) {
    this.full = 1;
    this.major = 0;
    this.patch = 0;
  }
}

export { compareVersion, versionOutOfDate, VersionNumber };
