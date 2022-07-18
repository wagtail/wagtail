import PropTypes from 'prop-types';
import React from 'react';

import { gettext } from '../../../utils/gettext';
import MediaBlock from './MediaBlock';
import { shortenLabel } from '../decorators/TooltipEntity';
/**
 * Editor block to display media and edit content.
 */
const EmbedBlock = (props) => {
  const { entity, onEditEntity, onRemoveEntity } = props.blockProps;
  const { url, title, thumbnail, providerName, authorName } = entity.getData();
  // Fallback text is used when there is no image available for the embed.
  // In those cases, it seems like author and provider name will always be present.
  const fallbackText = [authorName, providerName]
    .filter((text) => !!text)
    .map(shortenLabel)
    .join('\n');

  return (
    <MediaBlock {...props} src={thumbnail} alt="" fallbackText={fallbackText}>
      {url ? (
        <a
          className="Tooltip__link EmbedBlock__link"
          href={url}
          title={url}
          target="_blank"
          rel="noreferrer"
        >
          {title}
        </a>
      ) : null}
      <button
        className="button Tooltip__button"
        type="button"
        onClick={onEditEntity}
      >
        {gettext('Edit')}
      </button>
      <button
        className="button button-secondary no Tooltip__button"
        onClick={onRemoveEntity}
      >
        {gettext('Delete')}
      </button>
    </MediaBlock>
  );
};

EmbedBlock.propTypes = {
  blockProps: PropTypes.shape({
    entity: PropTypes.object,
  }).isRequired,
};

export default EmbedBlock;
