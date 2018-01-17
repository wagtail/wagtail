import PropTypes from 'prop-types';
import React from 'react';

import { STRINGS } from '../../../config/wagtailConfig';

import MediaBlock from '../blocks/MediaBlock';

const propTypes = {
  blockProps: PropTypes.shape({
    entity: PropTypes.object,
  }).isRequired,
};

/**
 * Editor block to display media and edit content.
 */
const EmbedBlock = props => {
  const { entity, onEditEntity, onRemoveEntity } = props.blockProps;
  const { url, title, thumbnail } = entity.getData();

  return (
    <MediaBlock {...props} src={thumbnail} alt="">
      <a
        className="Tooltip__link EmbedBlock__link"
        href={url}
        title={url}
        target="_blank"
        rel="noopener noreferrer"
      >
        {title}
      </a>

      <button className="button Tooltip__button" onClick={onEditEntity}>
        {STRINGS.EDIT}
      </button>

      <button className="button button-secondary no Tooltip__button" onClick={onRemoveEntity}>
        {STRINGS.DELETE}
      </button>
    </MediaBlock>
  );
};

EmbedBlock.propTypes = propTypes;

export default EmbedBlock;
