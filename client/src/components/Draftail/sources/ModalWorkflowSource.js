import PropTypes from 'prop-types';
import { Component } from 'react';
import { AtomicBlockUtils, Modifier, RichUtils, EditorState } from 'draft-js';
import { ENTITY_TYPE } from 'draftail';

import { STRINGS } from '../../../config/wagtailConfig';
import { getSelectionText } from '../DraftUtils';

const $ = global.jQuery;

const EMBED = 'EMBED';
const DOCUMENT = 'DOCUMENT';

const MUTABILITY = {};
MUTABILITY[ENTITY_TYPE.LINK] = 'MUTABLE';
MUTABILITY[DOCUMENT] = 'MUTABLE';
MUTABILITY[ENTITY_TYPE.IMAGE] = 'IMMUTABLE';
MUTABILITY[EMBED] = 'IMMUTABLE';

export const getChooserConfig = (entityType, entity, selectedText) => {
  let url;
  let urlParams;

  switch (entityType.type) {
  case ENTITY_TYPE.IMAGE:
    return {
      url: `${global.chooserUrls.imageChooser}?select_format=true`,
      urlParams: {},
      onload: global.IMAGE_CHOOSER_MODAL_ONLOAD_HANDLERS,
    };

  case EMBED:
    return {
      url: global.chooserUrls.embedsChooser,
      urlParams: {},
      onload: global.EMBED_CHOOSER_MODAL_ONLOAD_HANDLERS,
    };

  case ENTITY_TYPE.LINK:
    url = global.chooserUrls.pageChooser;
    urlParams = {
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
    };

  case DOCUMENT:
    return {
      url: global.chooserUrls.documentChooser,
      urlParams: {},
      onload: global.DOCUMENT_CHOOSER_MODAL_ONLOAD_HANDLERS,
    };

  default:
    return {
      url: null,
      urlParams: {},
      onload: {},
    };
  }
};

export const filterEntityData = (entityType, data) => {
  switch (entityType.type) {
  case ENTITY_TYPE.IMAGE:
    return {
      id: data.id,
      src: data.preview.url,
      alt: data.alt,
      format: data.format,
    };
  case EMBED:
    return {
      embedType: data.embedType,
      url: data.url,
      providerName: data.providerName,
      authorName: data.authorName,
      thumbnail: data.thumbnail,
      title: data.title,
    };
  case ENTITY_TYPE.LINK:
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
  case DOCUMENT:
    return {
      url: data.url,
      filename: data.filename,
      id: data.id,
    };
  default:
    return {};
  }
};

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

  componentDidMount() {
    const { onClose, entityType, entity, editorState } = this.props;
    const selectedText = getSelectionText(editorState);
    const { url, urlParams, onload } = getChooserConfig(entityType, entity, selectedText);

    $(document.body).on('hidden.bs.modal', this.onClose);

    // eslint-disable-next-line new-cap
    this.workflow = global.ModalWorkflow({
      url,
      urlParams,
      onload,
      responses: {
        imageChosen: this.onChosen,
        // Discard the first parameter (HTML) to only transmit the data.
        embedChosen: (_, data) => this.onChosen(data),
        documentChosen: this.onChosen,
        pageChosen: this.onChosen,
      },
      onError: () => {
        // eslint-disable-next-line no-alert
        window.alert(STRINGS.SERVER_ERROR);
        onClose();
      },
    });
  }

  componentWillUnmount() {
    this.workflow = null;

    $(document.body).off('hidden.bs.modal', this.onClose);
  }

  onChosen(data) {
    const { editorState, entityType, onComplete } = this.props;
    const content = editorState.getCurrentContent();
    const selection = editorState.getSelection();

    const entityData = filterEntityData(entityType, data);
    const mutability = MUTABILITY[entityType.type];
    const contentWithEntity = content.createEntity(entityType.type, mutability, entityData);
    const entityKey = contentWithEntity.getLastCreatedEntityKey();

    let nextState;

    if (entityType.block) {
      // Only supports adding entities at the moment, not editing existing ones.
      // See https://github.com/springload/draftail/blob/cdc8988fe2e3ac32374317f535a5338ab97e8637/examples/sources/ImageSource.js#L44-L62.
      // See https://github.com/springload/draftail/blob/cdc8988fe2e3ac32374317f535a5338ab97e8637/examples/sources/EmbedSource.js#L64-L91
      nextState = AtomicBlockUtils.insertAtomicBlock(editorState, entityKey, ' ');
    } else {
      // Replace text if the chooser demands it, or if there is no selected text in the first place.
      const shouldReplaceText = data.prefer_this_title_as_link_text || selection.isCollapsed();

      if (shouldReplaceText) {
        // If there is a title attribute, use it. Otherwise we inject the URL.
        const newText = data.title || data.url;
        const newContent = Modifier.replaceText(content, selection, newText, null, entityKey);
        nextState = EditorState.push(editorState, newContent, 'insert-characters');
      } else {
        nextState = RichUtils.toggleLink(editorState, selection, entityKey);
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
  onComplete: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
};

ModalWorkflowSource.defaultProps = {
  entity: null,
};

export default ModalWorkflowSource;
