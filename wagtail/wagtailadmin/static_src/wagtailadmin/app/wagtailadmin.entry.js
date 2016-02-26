import 'babel-polyfill';
import React from 'react';
import ReactDOM from 'react-dom';
import Explorer, { store } from 'components/explorer';

import { Provider } from 'react-redux'


document.addEventListener('DOMContentLoaded', e => {
  const top = document.querySelector('.wrapper');
  const div = document.createElement('div');
  const trigger = document.querySelector('[data-explorer-menu-url]');

  let rect = trigger.getBoundingClientRect();

  top.parentNode.appendChild(div);

  ReactDOM.render(
    <Provider store={store}>
      <Explorer fill={true} top={0} left={rect.right} />
    </Provider>,
    div
  );

  trigger.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    // Non-react access to store
    store.dispatch({ type: 'TOGGLE_EXPLORER' });
  });

});
