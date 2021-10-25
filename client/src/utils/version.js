function compareVersion(versionA, versionB) {
  const trailingZeroRe = /(\.0)+[^.]*$/;
  const va = (versionA + '').replace(trailingZeroRe, '').split('.');
  const vb = (versionB + '').replace(trailingZeroRe, '').split('.');
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
  return compareVersion(latestVersion, currentVersion) > 0;
}

export { compareVersion, versionOutOfDate };
