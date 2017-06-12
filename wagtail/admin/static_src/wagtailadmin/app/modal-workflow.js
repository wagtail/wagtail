import React from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';
import { createStore, applyMiddleware, compose } from 'redux';
import thunkMiddleware from 'redux-thunk';

import PageChooser from 'wagtail-client/src/components/choosers/page/PageChooser';
import pageChooser from 'wagtail-client/src/components/choosers/page/reducers';

// TODO Implement missing `canChooseRoot` param.
// TODO Implement missing `userPerms` param.
export function createPageChooser(id, restrictPageTypes, initialParentPageId) {
  const chooserElement = document.getElementById(`${id}-chooser`);
  const pageTitleElement = chooserElement.querySelector('.title');
  const editLinkElement = chooserElement.querySelector('.edit-link');
  const inputElement = document.getElementById(id);
  const chooseButtons = chooserElement.querySelectorAll('.action-choose');
  const clearButton = chooserElement.querySelector('.action-clear');

  // A few hacks to get restrictPageTypes into the correct format
  // eslint-disable-next-line no-param-reassign
  restrictPageTypes = restrictPageTypes
    .map(pageType => pageType.toLowerCase())
    .filter(pageType => pageType !== 'wagtailcore.page');

  if (restrictPageTypes.length === 0) {
    // eslint-disable-next-line no-param-reassign
    restrictPageTypes = null;
  }

  Array.prototype.slice.call(chooseButtons).forEach((chooseButton) => {
    chooseButton.addEventListener('click', () => {
      // Modal element might not exist when createPageChooser is called,
      // so we look it up in the event handler instead
      const modalPlacement = document.getElementById('react-modal');

      const middleware = [
        thunkMiddleware,
      ];

      const store = createStore(pageChooser, {}, compose(
        applyMiddleware(...middleware),
        // Expose store to Redux DevTools extension.
        window.devToolsExtension ? window.devToolsExtension() : f => f
      ));

      const onModalClose = () => {
        ReactDOM.render(<div />, modalPlacement);
      };

      const onPageChosen = (page) => {
        inputElement.value = page.id;
        pageTitleElement.innerHTML = page.title;  // FIXME
        chooserElement.classList.remove('blank');
        editLinkElement.href = `/admin/pages/${page.id}/edit/`;  // FIXME

        // Set initialParentPageId so if the chooser is open again,
        // it opens in the correct position
        if (page.meta.parent) {
          // eslint-disable-next-line no-param-reassign
          initialParentPageId = page.meta.parent.id;
        } else {
          // eslint-disable-next-line no-param-reassign
          initialParentPageId = null;
        }

        onModalClose();
      };

      ReactDOM.render((
        <Provider store={store}>
          <PageChooser
            onModalClose={onModalClose}
            onPageChosen={onPageChosen}
            initialParentPageId={initialParentPageId}
            restrictPageTypes={restrictPageTypes || null}
          />
        </Provider>
      ), modalPlacement);
    });
  });

  if (clearButton) {
    clearButton.addEventListener('click', () => {
      inputElement.value = '';
      chooserElement.classList.add('blank');
      // eslint-disable-next-line no-param-reassign
      initialParentPageId = null;
    });
  }
}
