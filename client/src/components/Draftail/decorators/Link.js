import PropTypes from 'prop-types';
import React from 'react';
import { Icon } from 'draftail';

const Link = ({ entityKey, contentState, children }) => {
  const { url } = contentState.getEntity(entityKey).getData();

  return (
    <span data-tooltip={entityKey} className="RichEditor-link">
      <Icon name={`icon-${url.indexOf('mailto:') !== -1 ? 'mail' : 'link'}`} />
      {children}
    </span>
  );
};

Link.propTypes = {
  entityKey: PropTypes.string.isRequired,
  contentState: PropTypes.object.isRequired,
  children: PropTypes.node.isRequired,
};

export default Link;
