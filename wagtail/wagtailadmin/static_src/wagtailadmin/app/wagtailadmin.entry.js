import React from 'react';
import ReactDOM from 'react-dom';
import Explorer from 'components/explorer';


document.addEventListener('DOMContentLoaded', e => {
  const top = document.querySelector('.wrapper');
  const div = document.createElement('div');
  const trigger = document.querySelector('[data-explorer-menu-url]');

  trigger.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();

    if (!div.childNodes.length) {
      ReactDOM.render(<Explorer position={trigger.getBoundingClientRect()} />, div);
    } else {
      ReactDOM.unmountComponentAtNode(div);
    }
  });

  top.parentNode.appendChild(div);
});
