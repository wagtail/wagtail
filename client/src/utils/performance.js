import React, { Component } from 'react';

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

      if (!!console.time) {
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

let perfComponent;

if (process.env.NODE_ENV !== 'production') {
  /**
   * Wraps the passed in `Component` in a higher-order component. It can then
   * measure the performance of every render of the `Component`.
   *
   * Can also be used as an ES2016 decorator.
   * @param  {ReactComponent} Component the component to wrap
   * @return {ReactComponent}           the wrapped component
   * See https://github.com/sheepsteak/react-perf-component
   */
  perfComponent = (Target) => {
    if (process.env.NODE_ENV === 'production') {
      return Target;
    }

    // eslint-disable-next-line global-require
    const ReactPerf = require('react-addons-perf');

    class Perf extends Component {
      componentDidMount() {
        ReactPerf.start();
      }

      componentDidUpdate() {
        ReactPerf.stop();

        const measurements = ReactPerf.getLastMeasurements();

        ReactPerf.printWasted(measurements);
        ReactPerf.start();
      }

      componentWillUnmount() {
        ReactPerf.stop();
      }

      render() {
        return <Target {...this.props} />;
      }
    }

    Perf.displayName = `perf(${Target.displayName || Target.name || 'Component'})`;
    Perf.WrappedComponent = Target;

    return Perf;
  };
}

export {
  perfMiddleware,
  perfComponent,
};
