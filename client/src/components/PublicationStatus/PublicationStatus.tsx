import PropTypes from 'prop-types';
import React from 'react';

/**
 * Displays the publication status of a page in a pill.
 */
const PublicationStatus = ({ status, live }) => (
  <span className={`c-status${live ? ' c-status--live' : ''}`}>{status}</span>
);

PublicationStatus.propTypes = {
  live: PropTypes.bool.isRequired,
  status: PropTypes.string.isRequired,
};

export default PublicationStatus;
