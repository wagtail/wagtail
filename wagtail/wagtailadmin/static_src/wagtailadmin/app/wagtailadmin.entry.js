import React from 'react';
import ReactDOM from 'react-dom';
import Explorer from 'components/explorer';


document.addEventListener('DOMContentLoaded', e => {
  const top = document.querySelector('.wrapper');
  const div = document.createElement('div');

  top.parentNode.appendChild(div);
  ReactDOM.render(<Explorer />, div);
});
