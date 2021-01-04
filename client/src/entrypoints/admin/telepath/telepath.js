/* eslint-disable indent */

window.telepath = {
    constructors: {},
    register(name, constructor) {
        this.constructors[name] = constructor;
    },
    unpack(objData) {
        var [constructorName, ...args] = objData;
        var constructor = this.constructors[constructorName];
        return new constructor(...args);
    }
};
