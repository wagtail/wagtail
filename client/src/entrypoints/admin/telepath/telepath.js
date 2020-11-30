/* eslint-disable */
window.telepath = {
    constructors: {},
    register: function(name, constructor) {
        this.constructors[name] = constructor;
    },
    unpack: function(objData) {
        var [constructorName, ...args] = objData;
        var constructor = this.constructors[constructorName];
        return new constructor(...args);
    }
};
