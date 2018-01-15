import PropTypes from 'prop-types';
import React from 'react';
import { AtomicBlockUtils, RichUtils } from 'draft-js';

const $ = global.jQuery;

class ModalSource extends React.Component {
  constructor(props) {
    super(props);
    this.onClose = this.onClose.bind(this);
    this.onConfirm = this.onConfirm.bind(this);
    this.onConfirmAtomicBlock = this.onConfirmAtomicBlock.bind(this);
  }

  componentWillUnmount() {
    $(document.body).off('hidden.bs.modal', this.onClose);
  }

  onConfirm(data) {
    const { editorState, entityType, onComplete } = this.props;
    const contentState = editorState.getCurrentContent();
    const contentStateWithEntity = contentState.createEntity(entityType.type, 'MUTABLE', data);
    const entityKey = contentStateWithEntity.getLastCreatedEntityKey();
    const nextState = RichUtils.toggleLink(editorState, editorState.getSelection(), entityKey);

    onComplete(nextState);
  }

  onConfirmAtomicBlock(data) {
    const { editorState, entityType, onComplete } = this.props;
    const contentState = editorState.getCurrentContent();
    const contentStateWithEntity = contentState.createEntity(entityType.type, 'IMMUTABLE', data);
    const entityKey = contentStateWithEntity.getLastCreatedEntityKey();
    const nextState = AtomicBlockUtils.insertAtomicBlock(editorState, entityKey, ' ');

    onComplete(nextState);
  }

  onClose(e) {
    const { onComplete } = this.props;
    e.preventDefault();

    onComplete();
  }

  render() {
    return null;
  }
}

ModalSource.propTypes = {
  editorState: PropTypes.object.isRequired,
  entityType: PropTypes.object.isRequired,
  // eslint-disable-next-line
  entity: PropTypes.object,
  onComplete: PropTypes.func.isRequired,
};

ModalSource.defaultProps = {
  entity: null,
};

export default ModalSource;
