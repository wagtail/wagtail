import React from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';
import { createStore, combineReducers, applyMiddleware, compose } from 'redux';
import thunkMiddleware from 'redux-thunk';

// import { perfMiddleware } from '../../utils/performance';
import Explorer from './Explorer';
import ExplorerToggle from './ExplorerToggle';
import explorer from './reducers/explorer';
import nodes from './reducers/nodes';

/**
 * Initialises the explorer component on the given nodes.
 */
const initExplorer = (explorerNode, toggleNode) => {
  const rootReducer = combineReducers({
    explorer,
    nodes,
  });

  const middleware = [
    thunkMiddleware,
  ];

  // Uncomment this to use performance measurements.
  // if (process.env.NODE_ENV !== 'production') {
  //   middleware.push(perfMiddleware);
  // }

  const store = createStore(rootReducer, {}, compose(
    applyMiddleware(...middleware),
    // Expose store to Redux DevTools extension.
    window.devToolsExtension ? window.devToolsExtension() : func => func
  ));

  const startPage = parseInt(toggleNode.getAttribute('data-explorer-start-page'), 10);

  ReactDOM.render((
    <Provider store={store}>
      <ExplorerToggle startPage={startPage}>{toggleNode.textContent}</ExplorerToggle>
    </Provider>
  ), toggleNode.parentNode);

  ReactDOM.render((
    <Provider store={store}>
      <Explorer />
    </Provider>
  ), explorerNode);
};

export default Explorer;

export {
  ExplorerToggle,
  initExplorer,
};
