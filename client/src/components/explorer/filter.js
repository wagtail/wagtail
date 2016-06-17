import React, { Component } from 'react';

const Filter = ({label, filter=null, activeFilter, onFilter}) => {
  let click = onFilter.bind(this, filter);
  let isActive =  activeFilter === filter;
  let cls = ['c-filter'];

  if (isActive) {
    cls.push('c-filter--active');
  }

  return (
    <span className={cls.join(' ')} onClick={click}>{label}</span>
  );
}


export default Filter;
