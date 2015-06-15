window.StructBlock = function(childInitializersByName) {
    return function(prefix) {
        for (var childName in childInitializersByName) {
            var childInitializer = childInitializersByName[childName];
            var childPrefix = prefix + '-' + childName;
            childInitializer(childPrefix);
        }
    };
};
