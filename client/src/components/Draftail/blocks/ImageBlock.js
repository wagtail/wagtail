import PropTypes from 'prop-types';
import React from 'react';

import { STRINGS } from '../../../config/wagtailConfig';

import MediaBlock from '../blocks/MediaBlock';

/**
 * Editor block to preview and edit images.
 */
const ImageBlock = props => {
  const { blockProps } = props;
  const { entity, onEditEntity, onRemoveEntity } = blockProps;
  const { src, alt } = entity.getData();
  let altLabel = STRINGS.DECORATIVE_IMAGE;
  if (alt) {
    altLabel = `${STRINGS.ALT_TEXT}: “${alt}”`;
  }

  return (
    <MediaBlock {...props} src={src} alt="">
      <p className="ImageBlock__alt">{altLabel}</p>

      <button className="button Tooltip__button" type="button" onClick={onEditEntity}>
        {STRINGS.EDIT}
      </button>
      <button className="button button-secondary no Tooltip__button" onClick={onRemoveEntity}>
        {STRINGS.DELETE}
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
