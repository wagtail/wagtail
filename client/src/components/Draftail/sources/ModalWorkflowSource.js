import PropTypes from 'prop-types';
import { Component } from 'react';
import { AtomicBlockUtils, Modifier, RichUtils, EditorState } from 'draft-js';
import { ENTITY_TYPE, DraftUtils } from 'draftail';

import { gettext } from '../../../utils/gettext';
import { getSelectionText } from '../DraftUtils';

const $ = global.jQuery;

const EMBED = 'EMBED';
const DOCUMENT = 'DOCUMENT';

const MUTABILITY = {};
MUTABILITY[ENTITY_TYPE.LINK] = 'MUTABLE';
MUTABILITY[DOCUMENT] = 'MUTABLE';
MUTABILITY[ENTITY_TYPE.IMAGE] = 'IMMUTABLE';
MUTABILITY[EMBED] = 'IMMUTABLE';

/**
 * Interfaces with Wagtail's ModalWorkflow to open the chooser,
 * and create new content in Draft.js based on the data.
 */
class ModalWorkflowSource extends Component {
  constructor(props) {
    super(props);

    this.onChosen = this.onChosen.bind(this);
    this.onClose = this.onClose.bind(this);
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  getChooserConfig(entity, selectedText) {
    throw new TypeError(
      'Subclasses of ModalWorkflowSource must implement getChooserConfig',
    );
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  filterEntityData(data) {
    throw new TypeError(
      'Subclasses of ModalWorkflowSource must implement filterEntityData',
    );
  }

  componentDidMount() {
    const { onClose, entity, editorState } = this.props;
    const selectedText = getSelectionText(editorState);
    const { url, urlParams, onload, responses } = this.getChooserConfig(
      entity,
      selectedText,
    );

    $(document.body).on('hidden.bs.modal', this.onClose);

    this.workflow = global.ModalWorkflow({
      url,
      urlParams,
      onload,
      responses,
      onError: () => {
        // eslint-disable-next-line no-alert
        window.alert(gettext('Server Error'));
        onClose();
      },
    });
  }

  componentWillUnmount() {
    this.workflow = null;

    $(document.body).off('hidden.bs.modal', this.onClose);
  }

  onChosen(data) {
    const { editorState, entity, entityKey, entityType, onComplete } =
      this.props;
    const content = editorState.getCurrentContent();
    const selection = editorState.getSelection();
    const entityData = this.filterEntityData(data);
    const mutability = MUTABILITY[entityType.type];

    let nextState;
    if (entityType.block) {
      if (entity && entityKey) {
        // Replace the data for the currently selected block
        const blockKey = selection.getAnchorKey();
        const block = content.getBlockForKey(blockKey);
        nextState = DraftUtils.updateBlockEntity(
          editorState,
          block,
          entityData,
        );
      } else {
        // Add new entity if there is none selected
        const contentWithEntity = content.createEntity(
          entityType.type,
          mutability,
          entityData,
        );
        const newEntityKey = contentWithEntity.getLastCreatedEntityKey();
        nextState = AtomicBlockUtils.insertAtomicBlock(
          editorState,
          newEntityKey,
          ' ',
        );
      }
    } else {
      const contentWithEntity = content.createEntity(
        entityType.type,
        mutability,
        entityData,
      );
      const newEntityKey = contentWithEntity.getLastCreatedEntityKey();

      // Replace text if the chooser demands it, or if there is no selected text in the first place.
      const shouldReplaceText =
        data.prefer_this_title_as_link_text || selection.isCollapsed();
      if (shouldReplaceText) {
        // If there is a title attribute, use it. Otherwise we inject the URL.
        const newText = data.title || data.url;
        const newContent = Modifier.replaceText(
          content,
          selection,
          newText,
          null,
          newEntityKey,
        );
        nextState = EditorState.push(
          editorState,
          newContent,
          'insert-characters',
        );
      } else {
        nextState = RichUtils.toggleLink(editorState, selection, newEntityKey);
      }
    }

    // IE11 crashes when rendering the new entity in contenteditable if the modal is still open.
    // Other browsers do not mind. This is probably a focus management problem.
    // From the user's perspective, this is all happening too fast to notice either way.
    this.workflow.close();

    onComplete(nextState);
  }

  onClose(e) {
    const { onClose } = this.props;
    e.preventDefault();

    onClose();
  }

  render() {
    return null;
  }
}

ModalWorkflowSource.propTypes = {
  editorState: PropTypes.object.isRequired,
  entityType: PropTypes.object.isRequired,
  entity: PropTypes.object,
  entityKey: PropTypes.string,
  onComplete: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
};

ModalWorkflowSource.defaultProps = {
  entity: null,
};

class ImageModalWorkflowSource extends ModalWorkflowSource {
  getChooserConfig(entity) {
    let url;
    let urlParams;

    if (entity) {
      const data = entity.getData();
      url = `${global.chooserUrls.imageChooser}${data.id}/select_format/`;
      urlParams = {
        format: data.format,
        alt_text: data.alt,
      };
    } else {
      url = `${global.chooserUrls.imageChooser}?select_format=true`;
      urlParams = {};
    }
    return {
      url,
      urlParams,
      onload: global.IMAGE_CHOOSER_MODAL_ONLOAD_HANDLERS,
      responses: {
        imageChosen: this.onChosen,
      },
    };
  }

  filterEntityData(data) {
    return {
      id: data.id,
      src: data.preview.url,
      alt: data.alt,
      format: data.format,
    };
  }
}

class EmbedModalWorkflowSource extends ModalWorkflowSource {
  getChooserConfig(entity) {
    const urlParams = {};

    if (entity) {
      urlParams.url = entity.getData().url;
    }
    return {
      url: global.chooserUrls.embedsChooser,
      urlParams,
      onload: global.EMBED_CHOOSER_MODAL_ONLOAD_HANDLERS,
      responses: {
        // Discard the first parameter (HTML) to only transmit the data.
        embedChosen: (_, data) => this.onChosen(data),
      },
    };
  }

  filterEntityData(data) {
    return {
      embedType: data.embedType,
      url: data.url,
      providerName: data.providerName,
      authorName: data.authorName,
      thumbnail: data.thumbnail,
      title: data.title,
    };
  }
}

class LinkModalWorkflowSource extends ModalWorkflowSource {
  getChooserConfig(entity, selectedText) {
    let url = global.chooserUrls.pageChooser;
    const urlParams = {
      page_type: 'wagtailcore.page',
      allow_external_link: true,
      allow_email_link: true,
      allow_phone_link: true,
      allow_anchor_link: true,
      link_text: selectedText,
    };

    if (entity) {
      const data = entity.getData();

      if (data.id) {
        if (data.parentId !== null) {
          url = `${global.chooserUrls.pageChooser}${data.parentId}/`;
        } else {
          url = global.chooserUrls.pageChooser;
        }
      } else if (data.url.startsWith('mailto:')) {
        url = global.chooserUrls.emailLinkChooser;
        urlParams.link_url = data.url.replace('mailto:', '');
      } else if (data.url.startsWith('tel:')) {
        url = global.chooserUrls.phoneLinkChooser;
        urlParams.link_url = data.url.replace('tel:', '');
      } else if (data.url.startsWith('#')) {
        url = global.chooserUrls.anchorLinkChooser;
        urlParams.link_url = data.url.replace('#', '');
      } else {
        url = global.chooserUrls.externalLinkChooser;
        urlParams.link_url = data.url;
      }
    }

    return {
      url,
      urlParams,
      onload: global.PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS,
      responses: {
        pageChosen: this.onChosen,
      },
    };
  }

  filterEntityData(data) {
    if (data.id) {
      return {
        url: data.url,
        id: data.id,
        parentId: data.parentId,
      };
    }

    return {
      url: data.url,
    };
  }
}

class DocumentModalWorkflowSource extends ModalWorkflowSource {
  getChooserConfig() {
    return {
      url: global.chooserUrls.documentChooser,
      urlParams: {},
      onload: global.DOCUMENT_CHOOSER_MODAL_ONLOAD_HANDLERS,
      responses: {
        documentChosen: this.onChosen,
      },
    };
  }

  filterEntityData(data) {
    return {
      url: data.url,
      filename: data.filename,
      id: data.id,
    };
  }
}

export {
  ModalWorkflowSource,
  ImageModalWorkflowSource,
  EmbedModalWorkflowSource,
  LinkModalWorkflowSource,
  DocumentModalWorkflowSource,
};
