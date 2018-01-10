import PropTypes from 'prop-types';
import React from 'react';

import Icon from '../../Icon/Icon';

import TooltipEntity from '../decorators/TooltipEntity';

const Document = props => {
  const { entityKey, contentState } = props;
  const { url } = contentState.getEntity(entityKey).getData();
  return (
    <TooltipEntity
      {...props}
      icon={<Icon name="doc-full" />}
      label={url.replace(/(^\w+:|^)\/\//, '').split('/')[0]}
    />
  );
};

Document.propTypes = {
  entityKey: PropTypes.string.isRequired,
  contentState: PropTypes.object.isRequired,
};

export default Document;
