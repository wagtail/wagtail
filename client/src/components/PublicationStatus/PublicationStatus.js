import React from 'react';

const PublicationStatus = ({ status }) => (status ? (
  <span className={`o-pill c-status${status.live ? ' c-status--live' : ''}`}>
    {status.status}
  </span>
) : null);

PublicationStatus.propTypes = {
  status: React.PropTypes.object,
};

export default PublicationStatus;
