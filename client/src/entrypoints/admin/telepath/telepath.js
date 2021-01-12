/* eslint-disable dot-notation */

class Telepath {
  constructor() {
    this.constructors = {};
  }

  register(name, constructor) {
    this.constructors[name] = constructor;
  }

  unpackAsDict(objData) {
    const result = [];
    for (const [key, val] of Object.entries(objData)) {
      result[key] = this.unpack(val);
    }
    return result;
  }

  unpack(objData) {
    if (objData === null || typeof(objData) !== 'object') {
      /* primitive value - return unchanged */
      return objData;
    }

    if (Array.isArray(objData)) {
      /* unpack recursively */
      return objData.map(item => this.unpack(item));
    }

    /* objData is an object / dict - look for special key names _type and _dict */
    if ('_type' in objData) {
      /* handle as a custom type */
      const constructorId = objData['_type'];
      const constructor = this.constructors[constructorId];
      /* unpack arguments recursively */
      const args = objData['_args'].map(arg => this.unpack(arg));
      return new constructor(...args);
    }

    if ('_dict' in objData) {
      return this.unpackAsDict(objData['_dict']);
    }

    /* no special key names found, so unpack objData as a plain dict */
    return this.unpackAsDict(objData);
  }
}

window.telepath = new Telepath();
