import React from 'react';
import ReactDOM from 'react-dom';
import { createStore, applyMiddleware } from 'redux';
import { Provider } from 'react-redux';
import thunk from 'redux-thunk';
import { StreamField, streamFieldReducer } from 'react-streamfield';

const store = createStore(streamFieldReducer, applyMiddleware(thunk));

const init = (name, options, currentScript) => {
  // document.currentScript is not available in IE11. Use a fallback instead.
  const context = currentScript ? currentScript.parentNode : document.body;
  // If the field is not in the current context, look for it in the whole body.
  // Fallback for sequence.js jQuery eval-ed scripts running in document.head.
  const selector = `[name="${name}"]`;
  const field = (context.querySelector(selector)
                 || document.body.querySelector(selector));

  const wrapper = document.createElement('div');

  field.parentNode.appendChild(wrapper);

  ReactDOM.render(
    <Provider store={store}>
      <StreamField
        {...options}
        id={name}
      />
    </Provider>,
    wrapper
  );
};

export default {
  init,
};
