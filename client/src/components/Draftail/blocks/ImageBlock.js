import PropTypes from 'prop-types';
import React, { Component } from 'react';

import { STRINGS } from '../../../config/wagtailConfig';

import MediaBlock from '../blocks/MediaBlock';

/**
 * Editor block to preview and edit images.
 */
class ImageBlock extends Component {
  constructor(props) {
    super(props);

    this.onEditEntity = this.onEditEntity.bind(this);
  }

  onEditEntity(e) {
    const { blockProps } = this.props;
    const { entity, onEditEntity } = blockProps;

    e.preventDefault();
    e.stopPropagation();
    onEditEntity(entity);
  }

  render() {
    const { blockProps } = this.props;
    const { entity, onRemoveEntity } = blockProps;
    const { src, alt } = entity.getData();
    const altLabel = `${STRINGS.ALT_TEXT}: “${alt || ''}”`;

    return (
      <MediaBlock {...this.props} src={src} alt="">
        <p className="ImageBlock__alt">{altLabel}</p>

        <button className="button Tooltip__button" onClick={this.onEditEntity}>
          {STRINGS.EDIT}
        </button>
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
