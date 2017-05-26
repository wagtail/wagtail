import React from 'react';

/**
 * Displays the publication status of a page in a pill.
 */
const PublicationStatus = ({ status }) => (
  <span className={`o-pill c-status${status.live ? ' c-status--live' : ''}`}>
    {status.status}
  </span>
);

PublicationStatus.propTypes = {
  status: React.PropTypes.shape({
    live: React.PropTypes.bool.isRequired,
    status: React.PropTypes.string.isRequired,
  }).isRequired,
};

export default PublicationStatus;
