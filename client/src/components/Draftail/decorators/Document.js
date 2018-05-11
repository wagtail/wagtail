import PropTypes from 'prop-types';
import React from 'react';

import Icon from '../../Icon/Icon';

import TooltipEntity from '../decorators/TooltipEntity';

const documentIcon = <Icon name="doc-full" />;

const Document = props => {
  const { entityKey, contentState } = props;
  const data = contentState.getEntity(entityKey).getData();

  return (
    <TooltipEntity
      {...props}
      icon={documentIcon}
      label={data.filename || ''}
      url={data.url || ''}
    />
  );
};

Document.propTypes = {
  entityKey: PropTypes.string.isRequired,
  contentState: PropTypes.object.isRequired,
};

export default Document;
