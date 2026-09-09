/* eslint-disable dot-notation, no-param-reassign */
/**
 * Backport of cyclic-graph support from the upstream telepath-unpack fork.
 * Remove this file and the webpack alias once the fix is merged and released.
 * See: https://github.com/wagtail/telepath-unpack/pull/5
 */

class Telepath {
  constructor() {
    this.constructors = {};
  }

  register(name, constructor) {
    this.constructors[name] = constructor;
  }

  unpack(objData) {
    const packedValuesById = {};
    this.scanForIds(objData, packedValuesById);
    const valuesById = {};
    return this.unpackWithRefs(objData, packedValuesById, valuesById);
  }

  scanForIds(objData, packedValuesById) {
    /* descend into objData, indexing any objects with an _id in packedValuesById */

    if (objData === null || typeof objData !== 'object') {
      /* primitive value - nothing to scan */
      return;
    }

    if (Array.isArray(objData)) {
      /* scan recursively */
      objData.forEach((item) => this.scanForIds(item, packedValuesById));
      return;
    }

    /* objData is an object / dict - check for reserved key names */
    let hasReservedKeyNames = false;

    if ('_id' in objData) {
      hasReservedKeyNames = true;
      /* index object in packedValuesById */
      packedValuesById[objData['_id']] = objData;
    }

    if ('_type' in objData || '_val' in objData || '_ref' in objData) {
      hasReservedKeyNames = true;
    }

    if ('_list' in objData) {
      hasReservedKeyNames = true;
      /* scan list items recursively */
      objData['_list'].forEach((item) => this.scanForIds(item, packedValuesById));
    }

    if ('_args' in objData) {
      hasReservedKeyNames = true;
      /* scan arguments recursively */
      objData['_args'].forEach((item) => this.scanForIds(item, packedValuesById));
    }

    if ('_dict' in objData) {
      hasReservedKeyNames = true;
      /* scan dict items recursively */
      for (const [, val] of Object.entries(objData['_dict'])) {
        this.scanForIds(val, packedValuesById);
      }
    }

    if (!hasReservedKeyNames) {
      /* scan as a plain dict */
      for (const [, val] of Object.entries(objData)) {
        this.scanForIds(val, packedValuesById);
      }
    }
  }

  unpackWithRefs(objData, packedValuesById, valuesById) {
    if (objData === null || typeof objData !== 'object') {
      /* primitive value - return unchanged */
      return objData;
    }

    if (Array.isArray(objData)) {
      /* unpack recursively */
      return objData.map((item) =>
        this.unpackWithRefs(item, packedValuesById, valuesById),
      );
    }

    /* objData is an object / dict - check for reserved key names */
    let result;

    if ('_ref' in objData) {
      if (objData['_ref'] in valuesById) {
        /* use previously unpacked instance */
        result = valuesById[objData['_ref']];
      } else {
        /* look up packed object and unpack it; this will populate valuesById as a side effect */
        result = this.unpackWithRefs(
          packedValuesById[objData['_ref']],
          packedValuesById,
          valuesById,
        );
      }
    } else if ('_val' in objData) {
      result = objData['_val'];
    } else if ('_list' in objData) {
      /* Create the array before unpacking items so that any back-reference
       * resolved during unpacking finds it immediately, closing the cycle. */
      result = [];
      if ('_id' in objData) valuesById[objData['_id']] = result;
      result.push(
        ...objData['_list'].map((item) =>
          this.unpackWithRefs(item, packedValuesById, valuesById),
        ),
      );
    } else if ('_dict' in objData) {
      /* Create the dict before unpacking values for the same reason. */
      result = {};
      if ('_id' in objData) valuesById[objData['_id']] = result;
      for (const [key, val] of Object.entries(objData['_dict'])) {
        result[key] = this.unpackWithRefs(val, packedValuesById, valuesById);
      }
    } else if ('_type' in objData) {
      /* handle as a custom type */
      const constructorId = objData['_type'];
      const constructor = this.constructors[constructorId];
      if (typeof constructor !== 'function') {
        throw new Error(
          `telepath encountered unknown object type ${constructorId}`,
        );
      }
      if ('_id' in objData) {
        /* Install a placeholder before unpacking args so that any back-reference
         * resolved during arg unpacking finds it immediately, closing the cycle. */
        const placeholder = Object.create(constructor.prototype);
        valuesById[objData['_id']] = placeholder;
        const args = objData['_args'].map((arg) =>
          this.unpackWithRefs(arg, packedValuesById, valuesById),
        );
        Object.assign(placeholder, new constructor(...args));
        return placeholder;
      }
      result = new constructor(
        ...objData['_args'].map((arg) =>
          this.unpackWithRefs(arg, packedValuesById, valuesById),
        ),
      );
    } else if ('_id' in objData) {
      throw new Error('telepath encountered object with _id but no type specified');
    } else {
      /* no reserved key names found, so unpack objData as a plain dict and return */
      result = {};
      for (const [key, val] of Object.entries(objData)) {
        result[key] = this.unpackWithRefs(val, packedValuesById, valuesById);
      }
      return result;
    }

    if ('_id' in objData) {
      valuesById[objData['_id']] = result;
    }

    return result;
  }
}

module.exports = Telepath;
