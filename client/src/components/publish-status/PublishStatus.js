import React, { PropTypes } from 'react';

const PublishStatus = ({ status }) => {
  return status ? (
    <span className={`o-pill c-status${status.live ? ' c-status--live' : ''}`}>
      {status.status}
    </span>
  ) : null;
};

PublishStatus.propTypes = {
    status: PropTypes.object,
};

export default PublishStatus;
