import PropTypes from 'prop-types';
import React, { Component } from 'react';
import { DraftUtils } from 'draftail';

import { STRINGS } from '../../../config/wagtailConfig';

import MediaBlock from '../blocks/MediaBlock';

/**
 * Editor block to preview and edit images.
 */
class ImageBlock extends Component {
  constructor(props) {
    super(props);

    this.changeAlt = this.changeAlt.bind(this);
  }

  changeAlt(e) {
    const { block, blockProps } = this.props;
    const { editorState, onChange } = blockProps;

    const data = {
      alt: e.target.value,
    };

    onChange(DraftUtils.updateBlockEntity(editorState, block, data));
  }

  render() {
    const { blockProps } = this.props;
    const { entity, onRemoveEntity } = blockProps;
    const { src, alt } = entity.getData();
    const altLabel = `${STRINGS.ALT_TEXT}: “${alt || ''}”`;

    return (
      <MediaBlock {...this.props} src={src} alt="">
        <p className="ImageBlock__alt">{altLabel}</p>

        <button className="button button-secondary no Tooltip__button" onClick={onRemoveEntity}>
          {STRINGS.DELETE}
        </button>
      </MediaBlock>
    );
  }
}

ImageBlock.propTypes = {
  block: PropTypes.object.isRequired,
  blockProps: PropTypes.shape({
    editorState: PropTypes.object.isRequired,
    entity: PropTypes.object,
    onChange: PropTypes.func.isRequired,
  }).isRequired,
};

export default ImageBlock;
