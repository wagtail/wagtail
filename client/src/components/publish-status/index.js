import React, { Component, PropTypes } from 'react';

const PublishStatus = ({ status }) => {
  if (!status) {
    return null;
  }

  let classes = ['o-pill', 'c-status', 'c-status--' + status.status];

  return (
    <span className={classes.join('  ')}>
      {status.status}
    </span>
  );
}

export default PublishStatus;
