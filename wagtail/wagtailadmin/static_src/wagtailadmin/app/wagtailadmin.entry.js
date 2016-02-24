import React from 'react';
import ReactDOM from 'react-dom';
import { Explorer } from 'wagtail';


document.addEventListener('DOMContentLoaded', e => {
  const explorerLink = document.querySelector('[data-explorer-menu-url]');
  let div = document.createElement('div');

  explorerLink.parentNode.appendChild(div);

  ReactDOM.render(<Explorer />, div);
});
