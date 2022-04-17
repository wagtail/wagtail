// Returns the value of the first argument. All others are ignored.
function identity<T extends any[]>(...func: T): T[0] {
  return func[0];
}

interface Action<N, P, M> {
  type: N;
  payload: P;
  error?: boolean;
  meta?: M;
}

// Stolen from the following project (had a 18kb footprint at the time).
// https://github.com/acdlite/redux-actions/blob/79c68635fb1524c1b1cf8e2398d4b099b53ca8de/src/createAction.js
export function createAction<N extends string, T extends any[], P, M>(
  type: N,
  actionCreator: (...args: T) => P = identity,
  metaCreator?: (...args: T) => M,
): (...args: T) => Action<N, P, M> {
  return (...args) => {
    const action: Action<N, P, M> = {
      type,
      payload: actionCreator(...args),
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
