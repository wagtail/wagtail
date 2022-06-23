/* eslint-disable import/no-mutable-exports */
let perfMiddleware;

if (process.env.NODE_ENV !== 'production') {
  /**
   * Performance middleware for use with a Redux store.
   * Will log the time taken by every action across all
   * of the reducers of the store.
   */
  perfMiddleware = () => {
    /* eslint-disable no-console */
    // `next` is a function that takes an 'action' and sends it through to the 'reducers'.
    const middleware = (next) => (action) => {
      let result;

      if (console.time) {
        console.time(action.type);
        result = next(action);
        console.timeEnd(action.type);
      } else {
        result = next(action);
      }

      return result;
    };

    return middleware;
  };
}

export { perfMiddleware };
