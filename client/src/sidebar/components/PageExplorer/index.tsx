import { createStore, combineReducers, applyMiddleware, compose } from 'redux';
import thunkMiddleware from 'redux-thunk';

// import { perfMiddleware } from '../../utils/performance';
import Explorer from './PageExplorer';
import explorer from './reducers/explorer';
import nodes from './reducers/nodes';

const initPageExplorerStore = () => {
  const rootReducer = combineReducers({
    explorer,
    nodes,
  });

  const middleware = [thunkMiddleware];

  // Uncomment this to use performance measurements.
  // if (process.env.NODE_ENV !== 'production') {
  //   middleware.push(perfMiddleware);
  // }

  return createStore(
    rootReducer,
    {},
    compose(
      applyMiddleware(...middleware),
      // Expose store to Redux DevTools extension.
      window.__REDUX_DEVTOOLS_EXTENSION__
        ? window.__REDUX_DEVTOOLS_EXTENSION__()
        : (func) => func,
    ),
  );
};

export default Explorer;

export { initPageExplorerStore };
