// eslint-disable-next-line func-names
window.StructBlock = function (childInitializersByName) {
  // eslint-disable-next-line func-names
  return function (prefix) {
    // eslint-disable-next-line no-restricted-syntax, guard-for-in
    for (const childName in childInitializersByName) {
      const childInitializer = childInitializersByName[childName];
      const childPrefix = prefix + '-' + childName;
      childInitializer(childPrefix);
    }
  };
};
