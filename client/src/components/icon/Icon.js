import React from 'react';

const Icon = ({ name, className, title }) => (
  <span className={`icon icon-${name} ${className}`} aria-hidden={!title}>
    {title ? (
      <span className="visuallyhidden">
        {title}
      </span>
    ) : null}
  </span>
);

Icon.propTypes = {
  name: React.PropTypes.string.isRequired,
  className: React.PropTypes.string,
  title: React.PropTypes.string,
};

Icon.defaultProps = {
  className: '',
  title: null,
};

export default Icon;
