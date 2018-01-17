import PropTypes from 'prop-types';
import React from 'react';

import Icon from '../../Icon/Icon';

import TooltipEntity from '../decorators/TooltipEntity';

const documentIcon = <Icon name="doc-full" />;

const getFilename = (path) => {
  const splitPath = path.split('/');

  return splitPath[splitPath.length - 1];
};

const Document = props => {
  const { entityKey, contentState } = props;
  const { url } = contentState.getEntity(entityKey).getData();

  return (
    <TooltipEntity
      {...props}
      icon={documentIcon}
      label={getFilename(url)}
      url={url}
    />
  );
};

Document.propTypes = {
  entityKey: PropTypes.string.isRequired,
  contentState: PropTypes.object.isRequired,
};

export default Document;
