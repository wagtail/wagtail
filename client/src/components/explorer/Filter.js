import React from 'react';

// TODO Do not use a span for a clickable element.
const Filter = ({ label, filter = null, activeFilter, onFilter }) => (
  <span
    className={`c-filter${activeFilter === filter ? ' c-filter--active' : ''}`}
    onClick={onFilter.bind(this, filter)}
  >
    {label}
  </span>
);

Filter.propTypes = {
  label: React.PropTypes.string.isRequired,
  filter: React.PropTypes.string,
  activeFilter: React.PropTypes.string,
  onFilter: React.PropTypes.func.isRequired,
};

export default Filter;
