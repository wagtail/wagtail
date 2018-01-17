import ModalSource from './ModalSource';

import { STRINGS } from '../../../config/wagtailConfig';

const $ = global.jQuery;

// Plaster over Wagtail internals.
const buildInitialUrl = (entity, openAtParentId, canChooseRoot, pageTypes) => {
  // We can't destructure from the window object yet
  const pageChooser = global.chooserUrls.pageChooser;
  const emailLinkChooser = global.chooserUrls.emailLinkChooser;
  const externalLinkChooser = global.chooserUrls.externalLinkChooser;
  let url = pageChooser;

  if (openAtParentId) {
    url = `${url}${openAtParentId}/`;
  }

  const urlParams = {
    page_type: pageTypes.join(','),
    allow_external_link: true,
    allow_email_link: true,
    can_choose_root: canChooseRoot ? 'true' : 'false',
    // This does not initialise the modal with the currently selected text.
    // This will need to be implemented in the future.
    // See https://github.com/jpuri/draftjs-utils/blob/e81c0ae19c3b0fdef7e0c1b70d924398956be126/js/block.js#L106.
    link_text: '',
  };

  if (entity) {
    const data = entity.getData();

    // urlParams.link_text = data.title;

    if (data.id) {
      url = ` ${pageChooser}${data.parentId}/`;
    } else if (data.url.startsWith('mailto:')) {
      url = emailLinkChooser;
      urlParams.link_url = data.url.replace('mailto:', '');
    } else {
      url = externalLinkChooser;
      urlParams.link_url = data.url;
    }
  }

  return { url, urlParams };
};

class LinkSource extends ModalSource {
  constructor(props) {
    super(props);
    this.parseData = this.parseData.bind(this);
  }

  parseData(data) {
    const parsedData = {
      url: data.url,
    };

    if (data.id) {
      parsedData.id = data.id;
      parsedData.parentId = data.parentId;
    }

    this.onConfirm(parsedData, data.title, data.prefer_this_title_as_link_text);
  }

  componentDidMount() {
    const { entity, onClose } = this.props;
    const openAtParentId = false;
    const canChooseRoot = false;
    const pageTypes = ['wagtailcore.page'];
    const { url, urlParams } = buildInitialUrl(entity, openAtParentId, canChooseRoot, pageTypes);

    $(document.body).on('hidden.bs.modal', this.onClose);

    // eslint-disable-next-line new-cap
    window.ModalWorkflow({
      url,
      urlParams,
      responses: {
        pageChosen: this.parseData,
      },
      onError: () => {
        // eslint-disable-next-line no-alert
        window.alert(STRINGS.SERVER_ERROR);
        onClose();
      },
    });
  }
}

export default LinkSource;
