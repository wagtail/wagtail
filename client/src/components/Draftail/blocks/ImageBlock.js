import PropTypes from 'prop-types';
import React from 'react';

import { gettext } from '../../../utils/gettext';
import MediaBlock from './MediaBlock';

/**
 * Editor block to preview and edit images.
 */
const ImageBlock = (props) => {
  const { blockProps } = props;
  const { entity, onEditEntity, onRemoveEntity } = blockProps;
  const { src, alt } = entity.getData();
  let altLabel = gettext('Decorative image');
  if (alt) {
    altLabel = `${gettext('Alt text')}: “${alt}”`;
  }

  return (
    <MediaBlock {...props} src={src} alt="">
      <p className="ImageBlock__alt">{altLabel}</p>

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

ImageBlock.propTypes = {
  block: PropTypes.object.isRequired,
  blockProps: PropTypes.shape({
    editorState: PropTypes.object.isRequired,
    entity: PropTypes.object,
    onChange: PropTypes.func.isRequired,
  }).isRequired,
};

export default ImageBlock;
