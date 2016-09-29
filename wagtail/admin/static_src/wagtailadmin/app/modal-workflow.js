import React from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';
import { createStore, applyMiddleware, compose } from 'redux';
import thunkMiddleware from 'redux-thunk';

import PageChooser from 'components/choosers/page/PageChooser';
import pageChooser from 'components/choosers/page/reducers';


export function createPageChooser(id, restrictPageTypes, initialParentPageId, canChooseRoot) {
  let chooserElement = document.getElementById(`${id}-chooser`);
  let pageTitleElement = chooserElement.querySelector('.title');
  let editLinkElement = chooserElement.querySelector('.edit-link');
  let inputElement = document.getElementById(id);
  let chooseButtons = chooserElement.querySelectorAll('.action-choose');
  let clearButton = chooserElement.querySelector('.action-clear');

  // A few hacks to get restrictPageTypes into the correct format
  restrictPageTypes = restrictPageTypes.map((pageType) => pageType.toLowerCase());
  restrictPageTypes = restrictPageTypes.filter((pageType) => pageType != 'wagtailcore.page');
  if (restrictPageTypes.length == 0) { restrictPageTypes = null; }

  for (let chooseButton of chooseButtons) {
    chooseButton.addEventListener('click', function() {
      // Modal element might not exist when createPageChooser is called,
      // so we look it up in the event handler instead
      let modalPlacement = document.getElementById('react-modal');

      const middleware = [
        thunkMiddleware,
      ];

      const store = createStore(pageChooser, {}, compose(
        applyMiddleware(...middleware),
        // Expose store to Redux DevTools extension.
        window.devToolsExtension ? window.devToolsExtension() : f => f
      ));

      let onModalClose = () => {
        ReactDOM.render(<div />, modalPlacement);
      };

      let onPageChosen = (page) => {
        inputElement.value = page.id;
        pageTitleElement.innerHTML = page.title;  // FIXME
        chooserElement.classList.remove('blank');
        editLinkElement.href = `/admin/pages/${page.id}/edit/`;  // FIXME

        // Set initialParentPageId so if the chooser is open again,
        // it opens in the correct position
        if (page.meta.parent) {
          initialParentPageId = page.meta.parent.id;
        } else {
          initialParentPageId = null;
        }

        onModalClose();
      };

      ReactDOM.render(<Provider store={store}>
        <PageChooser onModalClose={onModalClose} onPageChosen={onPageChosen} initialParentPageId={initialParentPageId} restrictPageTypes={restrictPageTypes || null} />
      </Provider>, modalPlacement);
    });
  }

  if (clearButton) {
    clearButton.addEventListener('click', function() {
      inputElement.value = '';
      chooserElement.classList.add('blank');
      initialParentPageId = null
    });
  }
}
