const identity = func => func;

// Stolen from the following project (had a 18kb footprint at the time).
// https://github.com/acdlite/redux-actions/blob/79c68635fb1524c1b1cf8e2398d4b099b53ca8de/src/createAction.js
export function createAction(type, actionCreator, metaCreator) {
  const finalActionCreator = typeof actionCreator === 'function' ? actionCreator : identity;

  return (...args) => {
    const action = {
      type,
      payload: finalActionCreator(...args),
    };

    if (action.payload instanceof Error) {
      // Handle FSA errors where the payload is an Error object. Set error.
      action.error = true;
    }

    if (typeof metaCreator === 'function') {
      action.meta = metaCreator(...args);
    }

    return action;
  };
}
