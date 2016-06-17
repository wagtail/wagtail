import React from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';
import { createStore, applyMiddleware, compose } from 'redux';
import thunkMiddleware from 'redux-thunk';

import Explorer from 'components/explorer/Explorer';
import ExplorerToggle from 'components/explorer/ExplorerToggle';
import rootReducer from 'components/explorer/reducers';

const initExplorer = () => {
  const explorerNode = document.querySelector('#explorer');
  const toggleNode = document.querySelector('[data-explorer-menu-url]');

  if (explorerNode && toggleNode) {
    const middleware = [
      thunkMiddleware,
    ];

    const store = createStore(rootReducer, {}, compose(
      applyMiddleware(...middleware),
      // Expose store to Redux DevTools extension.
      window.devToolsExtension ? window.devToolsExtension() : f => f
    ));

    const toggle = (
      <Provider store={store}>
        <ExplorerToggle>{toggleNode.innerText}</ExplorerToggle>
      </Provider>
    );

    const explorer = (
      <Provider store={store}>
        <Explorer type="sidebar" defaultPage={1} />
      </Provider>
    );

    ReactDOM.render(toggle, toggleNode.parentNode);
    ReactDOM.render(explorer, explorerNode);
  }
};

/**
 * Admin JS entry point. Add in here code to run once the page is loaded.
 */
document.addEventListener('DOMContentLoaded', () => {
  initExplorer();
});
