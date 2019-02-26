import React from 'react';
import ReactDOM from 'react-dom';
import { createStore, applyMiddleware } from 'redux';
import { Provider } from 'react-redux';
import thunk from 'redux-thunk';
import { StreamField, streamFieldReducer } from 'react-streamfield';

const store = createStore(streamFieldReducer, applyMiddleware(thunk));

export const initStreamField = () => {
  for (const streamfieldNode of document.querySelectorAll('script[data-streamfield]')) {
    const newNode = streamfieldNode.parentNode.insertBefore(document.createElement('div'), streamfieldNode);
    const id = streamfieldNode.getAttribute('data-streamfield');

    ReactDOM.render(
      <Provider store={store}>
        <StreamField
          {...JSON.parse(streamfieldNode.innerHTML)}
          id={id}
        />
      </Provider>,
      newNode
    );
  }
};
