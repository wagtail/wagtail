import PropTypes from 'prop-types';
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
  status: PropTypes.shape({
    live: PropTypes.bool.isRequired,
    status: PropTypes.string.isRequired,
  }).isRequired,
};

export default PublicationStatus;
